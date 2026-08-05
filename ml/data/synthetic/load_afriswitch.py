from datasets import load_dataset

# Note: This is a public dataset, no Hugging Face token required
# unless the specific dataset chosen from the collection shows as gated — if so,
# generate a free token at huggingface.co/settings/tokens and pass it via the
# `token=` parameter to load_dataset().

# Confirm exact dataset name from https://huggingface.co/collections/intronhealth/code-switching
afriswitch = load_dataset("intronhealth/afrispeech-dialog")
print(afriswitch)
print(afriswitch["train"][0])
