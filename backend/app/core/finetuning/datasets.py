datasets = {
    "general": [
        "Nemotron-Post-Training-Dataset-v2",
        "smoltalk2",
        "open-perfectblend",
        "orca-agentinstruct-1M-v1",
        "tulu3-sft-mixture",
        "FuseChat-Mixture",
    ],
    
    "math": [
        "MegaScience",
        "OpenThoughts3-1.2M",
        "NuminaMath-CoT",
        "AM-Thinking-v1-Distilled (Math)",
        "OmniThought-0528",
        "Orca-Math",
    ],
    
    "code": [
        "Ling-Coder-SFT",
        "rStar-Coder",
        "opc-sft-stage2",
        "AM-Thinking-v1-Distilled (Code)",
        "CodeFeedback-Filtered-Instruction",
        "synthetic_tex_to_sql",
    ],
    
    "instruction_following": [
        "AutoIF-instruct-61k-with-funcs",
        "ifeval-like-data",
        "tulu-3-sft-personas-instruction-following",
    ],
    
    "multilingual": [
        "luth-sft",
        "aya dataset",
        "M2Lingual",
    ],
    
    "agent_function_calling": [
        "xlam-function-calling-60k",
        "FunReason-MT",
        "hermes-function-calling-v1",
        "ToolACE",
        "APIGen-MT-5k",
    ],
    
    "real_conversations": [
        "WildChat-4.8M",
        "lmsys-chat-1m",
        "arena-human-preference-100k",
    ],
    
    "preference": [
        "Skywork-Reward-Preference-80K-v0.2",
        "ultrafeedback-binarized-preferences-cleaned",
        "Infinity-Preference",
        "Code-Preference-Pairs",
        "orpo-dpo-mix-40k",
        "HelpSteer3",
        "chatbot_arena_conversations",
        "FalseReject",
        "tulu-3-pref-personas-instruction-following",
        "Human-Like-DPO-Dataset",
    ]
}

tasks = [
    "general_instruction_tuning",
    "mathematical_reasoning",
    "code_generation_and_understanding",
    "instruction_following",
    "multilingual_understanding",
    "agent_and_function_calling",
    "real_world_conversation",
    "preference_alignment"
]