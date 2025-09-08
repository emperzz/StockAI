from typing import List
from langchain_core.messages import HumanMessage
from stockai.llm import LLM


def extract_text_from_image(image_path: str) -> str:
    """使用 PaddleOCR 提取图片文字，返回合并后的文本。

    懒加载依赖，避免未安装时影响其他功能。
    """
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "缺少 PaddleOCR 依赖，请安装 paddleocr 以启用图片文字提取"
        ) from exc

    ocr = PaddleOCR(use_angle_cls=True, lang="ch")
    # 与现有代码保持行为一致：使用 predict
    result = ocr.predict(image_path, cls=True)
    texts: List[str] = []
    for line in result or []:
        for seg in line or []:
            try:
                candidate = seg[1][0]
                if candidate:
                    texts.append(str(candidate))
            except Exception:
                continue
    return "\n".join(texts)


def extract_text_from_image_by_llm(image_url: str) -> str:
    """使用已配置的 LLM 模型进行多模态 OCR。

    要求模型支持图片输入（如部分 OpenAI/DeepSeek/Moonshot 等）。
    """
    model = LLM().get_model()
    messages = [
        HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                },
                {
                    "type": "text",
                    "text": "提取图片中的文字，并按图片排版以 Markdown 输出，不要额外解释。",
                },
            ]
        )
    ]
    ai_msg = model.invoke(messages)
    return getattr(ai_msg, "content", str(ai_msg))


