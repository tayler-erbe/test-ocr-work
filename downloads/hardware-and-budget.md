# Hardware and budget guide

Checked 27 October 2026. USD before tax/shipping. Planning estimates, not offers, purchase recommendations or measured cost savings. Use an existing approved GPU before buying another.

| Equipment budget | Starting workflow | Status and limits |
|---|---|---|
| Existing PC, no GPU purchase | Native PDF text, direct spreadsheet parsing, metadata, queue, review and CPU OCR baseline | No CPU OCR throughput benchmark here. Four vCPUs can contend across rendering, OCR, tokenization and ingestion; bound worker counts. |
| About $1,500–$2,500 complete 16 GB GPU workstation | One small parser at a time: PaddleOCR-VL or Nemotron Parse, with reviewed output | Planning allowance: about $800 GPU plus $700–$1,700 CPU/RAM/SSD/chassis. Not a tested build. Prefer 64 GB RAM and 1–2 TB NVMe for a pilot, adjusted for corpus size and copies. |
| About $6,000–$10,000 complete L4-compatible server | Small parsers and a serialized mid-size extraction candidate | $4,750 card listing plus $1,250–$5,250 host allowance. Confirm passive cooling, compatibility, power, drivers and warranty. No L4 run was performed. |
| About $16,000–$21,000 complete L40S-compatible server | More headroom for a quantized 32B extraction candidate and parser scheduling | $13,000 card listing plus $3,000–$8,000 host allowance. Not a procurement quote. No L40S run was performed. |

The consumer workstation is an alternative for readers starting from scratch, not this project's deployment target. Targets remain one L4 or one L40S. RTX 5090 measurements are the selection reference, not a requirement to buy a 5090.

## Price evidence

- [Best Buy, MSI RTX 5060 Ti 16 GB, SKU 6631084](https://www.bestbuy.com/product/msi-nvidia-geforce-geforce-rtx-5060-ti-16g-gaming-trio-oc-16gb-gddr7-pci-express-gen-5-graphics-card-black/6631084): displayed **$799.99**, **sold out** when checked. Price reference, not an available offer.
- [NVIDIA launch announcement](https://nvidianews.nvidia.com/news/nvidia-blackwell-geforce-rtx-arrives-for-every-gamer-starting-at-299): 16 GB card announced at **$429**. Historical starting MSRP is not today's purchasable price.
- [ServerSupply L4 listings](https://www.serversupply.com/GPU/GDDR6/24GB): NVIDIA 900-2G193-0000-000 and related new cards displayed **$4,750**. OEM bundles can differ in price and compatibility.
- [ServerSupply L40S](https://www.serversupply.com/GPU/GDDR6/48GB/NVIDIA/L40S_395278.htm): **$13,000**, availability **call**, estimated 2–3-week lead and limited seller warranty. Not confirmed stock or delivery.

Host allowances are explicit engineering estimates, not a sourced bill of materials. They exclude staffing, annotation, integration, security, support, energy, cooling, backup and recurring operation. Original laptop purchase cost was not verified. No ROI, dollars-per-document or cheaper-than-cloud claim is established.

## Memory planning

Approximate artifact sizes below were recorded in the source handoff. They are NOT total runtime VRAM. Framework reservations, images, KV cache, context, batching and other services need headroom.

| Job / artifact | Weight storage | L4, 24 GB nominal | L40S, 48 GB nominal |
|---|---:|---|---|
| Nemotron 3.5 Parse BF16 | 1.3 GB | Strong small-parser candidate | Strong small-parser candidate |
| PaddleOCR-VL-1.6 BF16 | 2 GB | Strong small-parser candidate | Strong small-parser candidate |
| olmOCR-2 7B FP8 | 9 GB | Candidate, reviewed prose only | Candidate, reviewed prose only |
| Qwen3-VL 8B FP8 | 10 GB | Chart/vision candidate; different from the laptop quantization | Candidate; pin exact artifact |
| GPT-OSS 20B MXFP4 | 13.8 GB local file | Bounded context/concurrency; peak not measured here | More headroom; peak/concurrency unmeasured |
| Qwen3 32B 4-bit / Qwen3-VL 32B AWQ | About 20 GB each | Tight; do not admit by weight size alone | Candidate subject to runtime admission |

Specifications: [NVIDIA L4](https://www.nvidia.com/en-us/data-center/l4/) and [NVIDIA L40S](https://www.nvidia.com/en-us/data-center/l40s/). Nominal memory is not all free memory. Do not promise simultaneous parser+32B residency or count a shared card as fully available. Default to one model/service at a time until the deployment owner admits an actual profile.

## What transfers

No target-card run is scheduled in this closeout; the laptop sweep is withdrawn. Stable weights and decoding are a reproducibility starting point, not a guarantee of identical outputs across kernels or hardware. Relative speed ranking can also change. Bandwidth ratios are architectural context, not pages-per-second predictions or a cost calculator.

The next implementation phase may perform service-installation admission and operational checks, distinct from extending model selection. Start with selected small parsers, bounded queues and reviewed outputs. Use larger extraction candidates where required.
