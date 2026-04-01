
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class DefaultTokens(BaseModel):
    """Default tokenization configuration"""
    unk_token: str = Field(default="[UNK]", description="Token for unknown words")
    pad_token: str = Field(default="[PAD]", description="Token for padding")
    cls_token: str = Field(default="[CLS]", description="Token for start of sequence")
    sep_token: str = Field(default="[SEP]", description="Token for end of sequence")
    mask_token: str = Field(default="[MASK]", description="Token for masked language modeling")

class TokenizationModelConfig(BaseModel):
    character_coverage: float = Field(default=0.9995)
    model_type: str = Field(default='unigram')
    model_name: str = Field(default='unigram')
    input_sentence_size: int = Field(default=1000000)
    shuffle_input_sentence: bool = Field(default=True)
    normalization_rule_name: str = Field(default='nmt_nfkc')
    remove_extra_whitespaces: bool = Field(default=True)
    model_path: str = Field(default="sentencepiece.model", description="Path to save the trained tokenizer model")
    


class TokenizationConfig(BaseModel):
    """Tokenization configuration model"""
    tokenizer_type: str = Field(default="bpe", description="Type of tokenizer to train (bpe, wordpiece, unigram)")
    vocab_size: int = Field(default=32000, ge=1000, le=100000, description="Vocabulary size for the tokenizer")
    dataset_path: str = Field(default="", description="Path to the dataset for training the tokenizer")
    tokenizer_path: Optional[str] = Field(default=None)
    default_tokens: DefaultTokens = Field(default_factory=DefaultTokens, description="Default tokens for the tokenizer")
    tokenization_model_config: TokenizationModelConfig = Field(default_factory=TokenizationModelConfig, description="Model configuration for the tokenizer")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for tokenizer training")




