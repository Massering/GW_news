import os
import logging
from typing import Optional

import torch
from dotenv import load_dotenv
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)

logger = logging.getLogger(__name__)

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN environment variable is not set")

MODEL_NAME = "ai-forever/rugpt3large_based_on_gpt2"
MAX_INPUT_CHARS = 4000


class LLMService:
    def __init__(
            self,
            model_name: str = MODEL_NAME,
            hf_token: Optional[str] = None,
    ):
        self.model_name = model_name
        self.hf_token = hf_token or HF_TOKEN

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info("Using device: %s", self.device)

        self.tokenizer = None
        self.model = None

        self._load_model()

    def _load_model(self):
        logger.info("Loading tokenizer: %s", self.model_name)

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            token=self.hf_token,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        logger.info("Loading model: %s", self.model_name)

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            token=self.hf_token,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        )

        self.model.to(self.device)
        self.model.eval()

        logger.info("Model loaded successfully")

    @torch.inference_mode()
    def query(self, prompt: str) -> str:
        prompt = (
            "Напиши краткую историческую сводку по газетному тексту.\n\n"
            f"{prompt}\n\n"
            "Краткая сводка:"
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        outputs = self.model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],

            max_new_tokens=80,

            do_sample=True,
            temperature=0.25,
            top_p=0.85,
            top_k=40,

            repetition_penalty=1.2,
            no_repeat_ngram_size=3,

            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]

        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        )

        return response.strip()


llm_service = LLMService()


def LLM_query(full_prompt: str) -> str:
    cropped_prompt = full_prompt[:MAX_INPUT_CHARS]
    return llm_service.query(cropped_prompt)
