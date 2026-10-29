# OCR vision evaluation (vision-v1): merged desktop + laptop results

Contract: prompts `a579532922ca`, scorers `d438bf722d3a`, cases v1 `d92bcbc12d72`, confirm `a8e2b349e391`.
Model labels are `model@side [variant]`. Failed cases count as zero. No model graded another model.

## Chart questions (ChartQA, relaxed accuracy)

| model | cases | failed | correct | correct_human | correct_augmented | median s |
|---|---|---|---|---|---|---|
| ollama:qwen2.5vl:32b@desktop | 200 | 0 | 82.0% | 75.0% | 89.0% | 0.880 |
| ollama:qwen2.5vl:32b@desktop [expert] | 200 | 0 | 82.0% | 79.0% | 85.0% | 0.900 |
| ollama:qwen2.5vl:32b@desktop [selfcheck] | 200 | 0 | 87.0% | 84.0% | 90.0% | 1.610 |
| ollama:qwen2.5vl:32b@desktop [upscale] | 200 | 1 | 76.5% | 73.0% | 80.0% | 1.580 |
| ollama:qwen2.5vl:7b@desktop | 200 | 0 | 53.5% | 63.0% | 44.0% | 0.460 |
| ollama:qwen2.5vl:7b@desktop [expert] | 200 | 0 | 44.5% | 53.0% | 36.0% | 0.480 |
| ollama:qwen2.5vl:7b@desktop [selfcheck] | 200 | 1 | 80.0% | 75.0% | 85.0% | 0.640 |
| ollama:qwen2.5vl:7b@desktop [upscale] | 200 | 0 | 49.0% | 63.0% | 35.0% | 0.860 |
| ollama:qwen2.5vl:7b@laptop | 200 | 0 | 52.5% | 62.0% | 43.0% | 0.880 |
| ollama:qwen2.5vl:7b@laptop [expert] | 200 | 0 | 47.5% | 56.0% | 39.0% | 0.900 |
| ollama:qwen2.5vl:7b@laptop [selfcheck] | 200 | 1 | 79.0% | 74.0% | 84.0% | 1.480 |
| ollama:qwen2.5vl:7b@laptop [upscale] | 200 | 0 | 47.5% | 62.0% | 33.0% | 2.190 |
| ollama:qwen3-vl:8b-instruct@desktop | 200 | 0 | 78.0% | 64.0% | 92.0% | 0.520 |
| ollama:qwen3-vl:8b-instruct@desktop [expert] | 200 | 0 | 76.0% | 74.0% | 78.0% | 0.530 |
| ollama:qwen3-vl:8b-instruct@desktop [selfcheck] | 200 | 0 | 32.5% | 46.0% | 19.0% | 0.710 |
| ollama:qwen3-vl:8b-instruct@desktop [upscale] | 200 | 0 | 79.5% | 65.0% | 94.0% | 0.790 |
| ollama:qwen3-vl:8b-instruct@laptop | 200 | 0 | 79.5% | 67.0% | 92.0% | 1.430 |
| ollama:qwen3-vl:8b-instruct@laptop [expert] | 200 | 0 | 75.0% | 73.0% | 77.0% | 1.090 |
| ollama:qwen3-vl:8b-instruct@laptop [selfcheck] | 200 | 0 | 36.0% | 50.0% | 22.0% | 1.650 |
| ollama:qwen3-vl:8b-instruct@laptop [upscale] | 200 | 0 | 80.0% | 66.0% | 94.0% | 2.130 |
| ollama:qwen3.8:27b@desktop | 200 | 0 | 85.5% | 77.0% | 94.0% | 0.640 |
| ollama:qwen3.8:27b@desktop [expert] | 200 | 0 | 87.0% | 81.0% | 93.0% | 0.680 |
| ollama:qwen3.8:27b@desktop [hires] | 200 | 0 | 85.5% | 77.0% | 94.0% | 0.670 |
| ollama:qwen3.8:27b@desktop [selfcheck] | 200 | 0 | 39.5% | 41.0% | 38.0% | 0.960 |
| ollama:qwen3.8:27b@desktop [upscale] | 200 | 0 | 88.0% | 81.0% | 95.0% | 1.330 |
| openai:qwen3vl32b@desktop | 200 | 0 | 85.0% | 75.0% | 95.0% | 0.520 |
| openai:qwen3vl32b@desktop [expert] | 200 | 0 | 84.0% | 75.0% | 93.0% | 0.480 |
| openai:qwen3vl32b@desktop [hires] | 200 | 0 | 85.0% | 75.0% | 95.0% | 0.500 |
| openai:qwen3vl32b@desktop [selfcheck] | 200 | 0 | 91.0% | 88.0% | 94.0% | 1.400 |
| openai:qwen3vl32b@desktop [table only] | 200 | 0 | 81.0% | 70.0% | 92.0% | 0.360 |
| openai:qwen3vl32b@desktop [upscale] | 200 | 0 | 89.5% | 84.0% | 95.0% | 1.090 |

## Chart questions, held-out confirmation set

| model | cases | failed | correct | correct_human | correct_augmented | median s |
|---|---|---|---|---|---|---|
| ollama:qwen3.8:27b@desktop | 2022 | 0 | 83.3% | 71.7% | 94.5% | 0.640 |
| openai:qwen3vl32b@desktop | 2022 | 0 | 86.4% | 77.9% | 94.5% | 0.490 |
| openai:qwen3vl32b@desktop [tuned] | 2022 | 0 | 88.3% | 83.3% | 93.0% | 1.460 |

## Table transcription (TEDS, cell F1)

| model | cases | failed | teds | teds_structure | cell_f1 | numeric_recall | median s |
|---|---|---|---|---|---|---|---|
| ollama:qwen2.5vl:32b@desktop | 60 | 0 | 0.805 | 0.849 | 0.789 | 0.972 | 5.070 |
| ollama:qwen2.5vl:32b@desktop [expert] | 60 | 0 | 0.807 | 0.869 | 0.801 | 0.967 | 4.950 |
| ollama:qwen2.5vl:32b@desktop [selfcheck] | 60 | 0 | 0.770 | 0.817 | 0.790 | 0.967 | 5.830 |
| ollama:qwen2.5vl:32b@desktop [upscale] | 60 | 0 | 0.830 | 0.872 | 0.797 | 0.973 | 5.230 |
| ollama:qwen2.5vl:7b@desktop | 60 | 0 | 0.724 | 0.790 | 0.761 | 0.933 | 1.520 |
| ollama:qwen2.5vl:7b@desktop [expert] | 60 | 0 | 0.748 | 0.812 | 0.766 | 0.951 | 1.570 |
| ollama:qwen2.5vl:7b@desktop [selfcheck] | 60 | 0 | 0.752 | 0.820 | 0.767 | 0.940 | 1.830 |
| ollama:qwen2.5vl:7b@desktop [upscale] | 60 | 0 | 0.734 | 0.799 | 0.778 | 0.938 | 1.820 |
| ollama:qwen2.5vl:7b@laptop | 60 | 0 | 0.724 | 0.797 | 0.765 | 0.941 | 5.250 |
| ollama:qwen2.5vl:7b@laptop [expert] | 60 | 0 | 0.757 | 0.817 | 0.767 | 0.953 | 5.440 |
| ollama:qwen2.5vl:7b@laptop [selfcheck] | 60 | 0 | 0.749 | 0.817 | 0.765 | 0.939 | 5.780 |
| ollama:qwen2.5vl:7b@laptop [upscale] | 60 | 0 | 0.728 | 0.792 | 0.775 | 0.925 | 6.750 |
| ollama:qwen3-vl:8b-instruct@desktop | 60 | 0 | 0.819 | 0.862 | 0.788 | 0.950 | 1.880 |
| ollama:qwen3-vl:8b-instruct@desktop [expert] | 60 | 0 | 0.822 | 0.869 | 0.789 | 0.948 | 1.890 |
| ollama:qwen3-vl:8b-instruct@desktop [selfcheck] | 60 | 0 | 0.818 | 0.866 | 0.790 | 0.945 | 2.000 |
| ollama:qwen3-vl:8b-instruct@desktop [upscale] | 60 | 0 | 0.832 | 0.873 | 0.794 | 0.947 | 1.990 |
| ollama:qwen3-vl:8b-instruct@laptop | 60 | 0 | 0.818 | 0.861 | 0.788 | 0.944 | 8.540 |
| ollama:qwen3-vl:8b-instruct@laptop [expert] | 60 | 0 | 0.829 | 0.870 | 0.789 | 0.946 | 6.550 |
| ollama:qwen3-vl:8b-instruct@laptop [selfcheck] | 60 | 0 | 0.823 | 0.873 | 0.790 | 0.946 | 6.320 |
| ollama:qwen3-vl:8b-instruct@laptop [upscale] | 60 | 0 | 0.831 | 0.873 | 0.793 | 0.946 | 7.010 |
| ollama:qwen3.8:27b@desktop | 60 | 0 | 0.852 | 0.896 | 0.777 | 0.968 | 2.640 |
| ollama:qwen3.8:27b@desktop [expert] | 60 | 0 | 0.870 | 0.912 | 0.796 | 0.975 | 2.500 |
| ollama:qwen3.8:27b@desktop [hires] | 60 | 0 | 0.853 | 0.896 | 0.777 | 0.969 | 2.650 |
| ollama:qwen3.8:27b@desktop [selfcheck] | 60 | 0 | 0.847 | 0.892 | 0.792 | 0.971 | 2.580 |
| ollama:qwen3.8:27b@desktop [upscale] | 60 | 0 | 0.852 | 0.891 | 0.784 | 0.977 | 3.370 |
| openai:qwen3vl32b@desktop | 60 | 0 | 0.821 | 0.861 | 0.776 | 0.969 | 5.510 |
| openai:qwen3vl32b@desktop [expert] | 60 | 0 | 0.849 | 0.891 | 0.782 | 0.973 | 5.330 |
| openai:qwen3vl32b@desktop [hires] | 60 | 0 | 0.821 | 0.861 | 0.776 | 0.969 | 5.520 |
| openai:qwen3vl32b@desktop [selfcheck] | 60 | 0 | 0.828 | 0.872 | 0.779 | 0.955 | 5.700 |
| openai:qwen3vl32b@desktop [upscale] | 60 | 0 | 0.841 | 0.885 | 0.787 | 0.970 | 5.560 |

## Table transcription, held-out confirmation set

| model | cases | failed | teds | teds_structure | cell_f1 | numeric_recall | median s |
|---|---|---|---|---|---|---|---|
| ollama:qwen3.8:27b@desktop | 159 | 1 | 0.870 | 0.913 | 0.772 | 0.948 | 2.650 |
| openai:qwen3vl32b@desktop | 159 | 0 | 0.851 | 0.907 | 0.766 | 0.967 | 5.640 |
| openai:qwen3vl32b@desktop [tuned] | 159 | 0 | 0.841 | 0.893 | 0.759 | 0.967 | 5.650 |

## Chart data extraction (values within 5%)

| model | cases | failed | value_recall | value_precision | label_recall | median s |
|---|---|---|---|---|---|---|
| ollama:qwen2.5vl:32b@desktop | 60 | 0 | 0.721 | 0.720 | 0.949 | 3.290 |
| ollama:qwen2.5vl:32b@desktop [expert] | 60 | 0 | 0.723 | 0.735 | 0.846 | 3.730 |
| ollama:qwen2.5vl:32b@desktop [selfcheck] | 60 | 0 | 0.742 | 0.729 | 0.935 | 4.200 |
| ollama:qwen2.5vl:32b@desktop [upscale] | 60 | 0 | 0.683 | 0.677 | 0.944 | 4.000 |
| ollama:qwen2.5vl:7b@desktop | 60 | 0 | 0.715 | 0.700 | 0.607 | 0.990 |
| ollama:qwen2.5vl:7b@desktop [expert] | 60 | 3 | 0.533 | 0.516 | 0.578 | 1.040 |
| ollama:qwen2.5vl:7b@desktop [selfcheck] | 60 | 0 | 0.708 | 0.671 | 0.829 | 1.110 |
| ollama:qwen2.5vl:7b@desktop [upscale] | 60 | 3 | 0.784 | 0.783 | 0.593 | 1.430 |
| ollama:qwen2.5vl:7b@laptop | 60 | 2 | 0.650 | 0.635 | 0.587 | 2.580 |
| ollama:qwen2.5vl:7b@laptop [expert] | 60 | 4 | 0.541 | 0.535 | 0.579 | 2.860 |
| ollama:qwen2.5vl:7b@laptop [selfcheck] | 60 | 0 | 0.626 | 0.620 | 0.850 | 2.790 |
| ollama:qwen2.5vl:7b@laptop [upscale] | 60 | 2 | 0.636 | 0.627 | 0.676 | 3.870 |
| ollama:qwen3-vl:8b-instruct@desktop | 60 | 0 | 0.483 | 0.494 | 0.417 | 1.000 |
| ollama:qwen3-vl:8b-instruct@desktop [expert] | 60 | 0 | 0.915 | 0.921 | 0.804 | 1.500 |
| ollama:qwen3-vl:8b-instruct@desktop [selfcheck] | 60 | 0 | 0.930 | 0.959 | 0.921 | 1.610 |
| ollama:qwen3-vl:8b-instruct@desktop [upscale] | 60 | 0 | 0.643 | 0.653 | 0.593 | 1.520 |
| ollama:qwen3-vl:8b-instruct@laptop | 60 | 0 | 0.418 | 0.427 | 0.350 | 1.750 |
| ollama:qwen3-vl:8b-instruct@laptop [expert] | 60 | 0 | 0.900 | 0.899 | 0.816 | 4.180 |
| ollama:qwen3-vl:8b-instruct@laptop [selfcheck] | 60 | 0 | 0.930 | 0.958 | 0.921 | 4.420 |
| ollama:qwen3-vl:8b-instruct@laptop [upscale] | 60 | 0 | 0.630 | 0.637 | 0.583 | 4.490 |
| ollama:qwen3.8:27b@desktop | 60 | 0 | 0.864 | 0.859 | 0.963 | 2.100 |
| ollama:qwen3.8:27b@desktop [expert] | 60 | 1 | 0.730 | 0.721 | 0.963 | 2.050 |
| ollama:qwen3.8:27b@desktop [hires] | 60 | 0 | 0.864 | 0.859 | 0.963 | 2.160 |
| ollama:qwen3.8:27b@desktop [selfcheck] | 60 | 0 | 0.817 | 0.825 | 0.979 | 2.240 |
| ollama:qwen3.8:27b@desktop [upscale] | 60 | 2 | 0.884 | 0.881 | 0.944 | 2.720 |
| openai:qwen3vl32b@desktop | 60 | 0 | 0.901 | 0.906 | 0.912 | 3.940 |
| openai:qwen3vl32b@desktop [expert] | 60 | 0 | 0.893 | 0.906 | 0.929 | 3.750 |
| openai:qwen3vl32b@desktop [hires] | 60 | 0 | 0.901 | 0.906 | 0.912 | 3.780 |
| openai:qwen3vl32b@desktop [selfcheck] | 60 | 0 | 0.902 | 0.909 | 0.947 | 4.110 |
| openai:qwen3vl32b@desktop [upscale] | 60 | 0 | 0.902 | 0.916 | 0.905 | 4.600 |

## Prose crops (character error rate, lower is better)

| model | cases | failed | cer_completed | numeric_recall | numeric_precision | median s |
|---|---|---|---|---|---|---|
| ollama:qwen2.5vl:32b@desktop | 50 | 0 | 0.012 | 0.965 | 0.953 | 1.450 |
| ollama:qwen2.5vl:7b@desktop | 50 | 0 | 0.018 | 0.965 | 0.953 | 0.510 |
| ollama:qwen2.5vl:7b@laptop | 50 | 0 | 0.020 | 0.965 | 0.953 | 1.760 |
| ollama:qwen3-vl:8b-instruct@desktop | 50 | 0 | 0.012 | 0.965 | 0.953 | 0.610 |
| ollama:qwen3-vl:8b-instruct@laptop | 50 | 0 | 0.012 | 0.965 | 0.953 | 2.560 |
| ollama:qwen3.8:27b@desktop | 50 | 0 | 0.011 | 0.965 | 0.953 | 0.710 |
| openai:qwen3vl32b@desktop | 50 | 0 | 0.012 | 0.965 | 0.953 | 1.000 |

## Whole pages (word F1)

| model | cases | failed | word_f1 | numeric_recall | median s |
|---|---|---|---|---|---|
| openai:qwen3vl32b@desktop | 40 | 0 | 0.809 | 0.909 | 16.500 |
| openai:qwen3vl32b@desktop [layoutmask] | 40 | 0 | 0.895 | 0.720 | 11.870 |

## Layout (figures and tables, IoU >= 0.5)

| model | figure P | figure R | figure F1 | table P | table R | table F1 |
|---|---|---|---|---|---|---|
| openai:qwen3vl32b@desktop | 0.570 | 0.658 | 0.611 | 0.600 | 0.882 | 0.714 |
| yolo@desktop | 0.836 | 0.872 | 0.854 | 0.782 | 0.843 | 0.811 |

## Variants against baseline (paired, same cases)

| model | task | variant | cases | baseline | variant | change | 95% CI | better/worse | test | p | family | p (Holm) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ollama:qwen2.5vl:32b@desktop | chart_qa | expert | 200 | 0.82 | 0.82 | +0.0000 | [-0.04, 0.04] | 9/9 | exact McNemar | 1.0 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:32b@desktop | chart_qa | selfcheck | 200 | 0.82 | 0.87 | +0.0500 | [0.0, 0.1] | 18/8 | exact McNemar | 0.0755 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:32b@desktop | chart_qa | upscale | 200 | 0.82 | 0.765 | -0.0550 | [-0.105, 0.0] | 9/20 | exact McNemar | 0.0614 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:32b@desktop | chart_table | expert | 60 | 0.7214 | 0.7234 | +0.0020 | [-0.1149, 0.1169] | 10/11 | paired bootstrap | 0.966 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:32b@desktop | chart_table | selfcheck | 60 | 0.7214 | 0.7417 | +0.0203 | [-0.0781, 0.1174] | 9/6 | paired bootstrap | 0.66 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:32b@desktop | chart_table | upscale | 60 | 0.7214 | 0.6826 | -0.0388 | [-0.1011, 0.0127] | 4/5 | paired bootstrap | 0.157 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:32b@desktop | table | expert | 60 | 0.8046 | 0.8073 | +0.0027 | [-0.0326, 0.0331] | 14/11 | paired bootstrap | 0.804 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:32b@desktop | table | selfcheck | 60 | 0.8046 | 0.7697 | -0.0350 | [-0.0781, 0.0083] | 9/27 | paired bootstrap | 0.111 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:32b@desktop | table | upscale | 60 | 0.8046 | 0.8304 | +0.0258 | [-0.0007, 0.0585] | 17/8 | paired bootstrap | 0.062 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@desktop | chart_qa | expert | 200 | 0.535 | 0.445 | -0.0900 | [-0.135, -0.04] | 4/22 | exact McNemar | 0.0005 | exploratory | 0.032 | worse |
| ollama:qwen2.5vl:7b@desktop | chart_qa | selfcheck | 200 | 0.535 | 0.8 | +0.2650 | [0.19, 0.34] | 63/10 | exact McNemar | 0.0 | exploratory | 0.0 | better |
| ollama:qwen2.5vl:7b@desktop | chart_qa | upscale | 200 | 0.535 | 0.49 | -0.0450 | [-0.085, -0.005] | 5/14 | exact McNemar | 0.0636 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@desktop | chart_table | expert | 60 | 0.7153 | 0.5328 | -0.1825 | [-0.318, -0.0478] | 5/19 | paired bootstrap | 0.005 | exploratory | 0.29 | not significant |
| ollama:qwen2.5vl:7b@desktop | chart_table | selfcheck | 60 | 0.7153 | 0.7078 | -0.0075 | [-0.1192, 0.1044] | 8/9 | paired bootstrap | 0.907 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@desktop | chart_table | upscale | 60 | 0.7153 | 0.7837 | +0.0684 | [0.011, 0.1389] | 7/4 | paired bootstrap | 0.017 | exploratory | 0.9464 | not significant |
| ollama:qwen2.5vl:7b@desktop | table | expert | 60 | 0.724 | 0.7476 | +0.0236 | [-0.0114, 0.0649] | 21/11 | paired bootstrap | 0.223 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@desktop | table | selfcheck | 60 | 0.724 | 0.7524 | +0.0285 | [-0.0206, 0.0813] | 18/20 | paired bootstrap | 0.252 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@desktop | table | upscale | 60 | 0.724 | 0.7338 | +0.0098 | [-0.0212, 0.0478] | 11/14 | paired bootstrap | 0.635 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@laptop | chart_qa | expert | 200 | 0.525 | 0.475 | -0.0500 | [-0.09, -0.01] | 4/14 | exact McNemar | 0.0309 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@laptop | chart_qa | selfcheck | 200 | 0.525 | 0.79 | +0.2650 | [0.185, 0.34] | 64/11 | exact McNemar | 0.0 | exploratory | 0.0 | better |
| ollama:qwen2.5vl:7b@laptop | chart_qa | upscale | 200 | 0.525 | 0.475 | -0.0500 | [-0.095, -0.01] | 5/15 | exact McNemar | 0.0414 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@laptop | chart_qa_confirm2 | selfcheck | 1322 | 0.5575 | 0.7352 | +0.1778 | [0.1498, 0.2073] | 324/89 | exact McNemar | 0.0 | supporting_v2 | 0.0 | better |
| ollama:qwen2.5vl:7b@laptop | chart_qa_confirm2 | upscale | 1322 | 0.5575 | 0.5197 | -0.0378 | [-0.0552, -0.0212] | 44/94 | exact McNemar | 0.0 | supporting_v2 | 0.0001 | worse |
| ollama:qwen2.5vl:7b@laptop | chart_qa_confirm2 | vote3 | 1322 | 0.5575 | 0.6029 | +0.0454 | [0.0303, 0.0605] | 80/20 | exact McNemar | 0.0 | confirmatory_v2 | 0.0 | better |
| ollama:qwen2.5vl:7b@laptop | chart_qa_dev2 | selfcheck | 586 | 0.558 | 0.7696 | +0.2116 | [0.1672, 0.2543] | 162/38 | exact McNemar | 0.0 | exploratory_v2 | 0.0 | better |
| ollama:qwen2.5vl:7b@laptop | chart_qa_dev2 | upscale | 586 | 0.558 | 0.5102 | -0.0478 | [-0.0734, -0.0222] | 14/42 | exact McNemar | 0.0002 | exploratory_v2 | 0.0018 | worse |
| ollama:qwen2.5vl:7b@laptop | chart_qa_dev2 | vote3 | 586 | 0.558 | 0.6007 | +0.0427 | [0.0205, 0.0648] | 36/11 | exact McNemar | 0.0003 | exploratory_v2 | 0.0021 | better |
| ollama:qwen2.5vl:7b@laptop | chart_table | expert | 60 | 0.6497 | 0.5406 | -0.1091 | [-0.2478, 0.0364] | 7/20 | paired bootstrap | 0.116 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@laptop | chart_table | selfcheck | 60 | 0.6497 | 0.6256 | -0.0241 | [-0.1643, 0.115] | 11/15 | paired bootstrap | 0.678 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@laptop | chart_table | upscale | 60 | 0.6497 | 0.6359 | -0.0138 | [-0.1296, 0.1017] | 10/10 | paired bootstrap | 0.826 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@laptop | page_text_confirm2 | layoutmask | 80 | 0.7574 | 0.8428 | +0.0854 | [0.0385, 0.135] | 39/31 | paired bootstrap | 0.0 | confirmatory_v2 | 0.0 | better |
| ollama:qwen2.5vl:7b@laptop | table | expert | 60 | 0.7239 | 0.7574 | +0.0335 | [-0.0001, 0.0704] | 22/10 | paired bootstrap | 0.052 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@laptop | table | selfcheck | 60 | 0.7239 | 0.7491 | +0.0252 | [-0.0247, 0.0779] | 19/20 | paired bootstrap | 0.317 | exploratory | 1.0 | not significant |
| ollama:qwen2.5vl:7b@laptop | table | upscale | 60 | 0.7239 | 0.7284 | +0.0045 | [-0.0225, 0.0332] | 12/12 | paired bootstrap | 0.757 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@desktop | chart_qa | expert | 200 | 0.78 | 0.76 | -0.0200 | [-0.075, 0.035] | 13/17 | exact McNemar | 0.5847 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@desktop | chart_qa | selfcheck | 200 | 0.78 | 0.325 | -0.4550 | [-0.535, -0.375] | 9/100 | exact McNemar | 0.0 | exploratory | 0.0 | worse |
| ollama:qwen3-vl:8b-instruct@desktop | chart_qa | upscale | 200 | 0.78 | 0.795 | +0.0150 | [-0.01, 0.04] | 5/2 | exact McNemar | 0.4531 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@desktop | chart_table | expert | 60 | 0.4827 | 0.9154 | +0.4327 | [0.3014, 0.5664] | 28/3 | paired bootstrap | 0.0 | exploratory | 0.0 | better |
| ollama:qwen3-vl:8b-instruct@desktop | chart_table | selfcheck | 60 | 0.4827 | 0.9302 | +0.4475 | [0.3265, 0.5708] | 29/3 | paired bootstrap | 0.0 | exploratory | 0.0 | better |
| ollama:qwen3-vl:8b-instruct@desktop | chart_table | upscale | 60 | 0.4827 | 0.6429 | +0.1602 | [0.0581, 0.2755] | 11/5 | paired bootstrap | 0.005 | exploratory | 0.29 | not significant |
| ollama:qwen3-vl:8b-instruct@desktop | table | expert | 60 | 0.8186 | 0.8218 | +0.0032 | [-0.0178, 0.022] | 9/6 | paired bootstrap | 0.757 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@desktop | table | selfcheck | 60 | 0.8186 | 0.8181 | -0.0005 | [-0.0155, 0.0158] | 15/9 | paired bootstrap | 0.946 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@desktop | table | upscale | 60 | 0.8186 | 0.8321 | +0.0135 | [-0.0008, 0.0399] | 6/4 | paired bootstrap | 0.142 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa | expert | 200 | 0.795 | 0.75 | -0.0450 | [-0.095, 0.005] | 9/18 | exact McNemar | 0.1221 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa | selfcheck | 200 | 0.795 | 0.36 | -0.4350 | [-0.51, -0.35] | 9/96 | exact McNemar | 0.0 | exploratory | 0.0 | worse |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa | upscale | 200 | 0.795 | 0.8 | +0.0050 | [-0.025, 0.035] | 5/4 | exact McNemar | 1.0 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa_confirm2 | selfcheck | 1322 | 0.7496 | 0.323 | -0.4266 | [-0.4554, -0.3964] | 50/614 | exact McNemar | 0.0 | supporting_v2 | 0.0 | worse |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa_confirm2 | upscale | 1322 | 0.7496 | 0.7648 | +0.0151 | [0.003, 0.0272] | 44/24 | exact McNemar | 0.0205 | supporting_v2 | 0.0411 | better |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa_confirm2 | vote3 | 1322 | 0.7496 | 0.7481 | -0.0015 | [-0.0106, 0.0076] | 19/21 | exact McNemar | 0.8746 | confirmatory_v2 | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa_dev2 | selfcheck | 586 | 0.785 | 0.3225 | -0.4625 | [-0.5068, -0.4164] | 18/289 | exact McNemar | 0.0 | exploratory_v2 | 0.0 | worse |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa_dev2 | upscale | 586 | 0.785 | 0.7935 | +0.0085 | [-0.0102, 0.0273] | 18/13 | exact McNemar | 0.4731 | exploratory_v2 | 0.9463 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | chart_qa_dev2 | vote3 | 586 | 0.785 | 0.7799 | -0.0051 | [-0.0171, 0.0068] | 5/8 | exact McNemar | 0.5811 | exploratory_v2 | 0.9463 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | chart_table | expert | 60 | 0.4179 | 0.8999 | +0.4820 | [0.349, 0.5997] | 29/1 | paired bootstrap | 0.0 | exploratory | 0.0 | better |
| ollama:qwen3-vl:8b-instruct@laptop | chart_table | selfcheck | 60 | 0.4179 | 0.9296 | +0.5118 | [0.3876, 0.6394] | 33/2 | paired bootstrap | 0.0 | exploratory | 0.0 | better |
| ollama:qwen3-vl:8b-instruct@laptop | chart_table | upscale | 60 | 0.4179 | 0.6304 | +0.2125 | [0.0982, 0.3287] | 15/3 | paired bootstrap | 0.001 | exploratory | 0.059 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | page_text_confirm2 | layoutmask | 80 | 0.8283 | 0.838 | +0.0098 | [-0.0354, 0.0504] | 34/35 | paired bootstrap | 0.66 | confirmatory_v2 | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | table | expert | 60 | 0.8177 | 0.8285 | +0.0109 | [0.0007, 0.0254] | 9/4 | paired bootstrap | 0.018 | exploratory | 0.972 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | table | selfcheck | 60 | 0.8177 | 0.8231 | +0.0054 | [-0.0174, 0.0299] | 13/8 | paired bootstrap | 0.686 | exploratory | 1.0 | not significant |
| ollama:qwen3-vl:8b-instruct@laptop | table | upscale | 60 | 0.8177 | 0.8312 | +0.0136 | [-0.0006, 0.0392] | 8/4 | paired bootstrap | 0.128 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | chart_qa | expert | 200 | 0.855 | 0.87 | +0.0150 | [-0.02, 0.055] | 9/6 | exact McNemar | 0.6072 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | chart_qa | hires | 200 | 0.855 | 0.855 | +0.0000 | [0.0, 0.0] | 0/0 | exact McNemar | 1.0 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | chart_qa | selfcheck | 200 | 0.855 | 0.395 | -0.4600 | [-0.53, -0.385] | 3/95 | exact McNemar | 0.0 | exploratory | 0.0 | worse |
| ollama:qwen3.8:27b@desktop | chart_qa | upscale | 200 | 0.855 | 0.88 | +0.0250 | [-0.015, 0.07] | 12/7 | exact McNemar | 0.3593 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | chart_table | expert | 60 | 0.8639 | 0.7299 | -0.1340 | [-0.2507, -0.0179] | 4/12 | paired bootstrap | 0.018 | exploratory | 0.972 | not significant |
| ollama:qwen3.8:27b@desktop | chart_table | hires | 60 | 0.8639 | 0.8639 | +0.0000 | [0.0, 0.0] | 0/0 | paired bootstrap | 1.0 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | chart_table | selfcheck | 60 | 0.8639 | 0.817 | -0.0469 | [-0.1296, 0.0239] | 3/7 | paired bootstrap | 0.183 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | chart_table | upscale | 60 | 0.8639 | 0.8837 | +0.0198 | [-0.0495, 0.1003] | 6/2 | paired bootstrap | 0.526 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | table | expert | 60 | 0.8525 | 0.8695 | +0.0170 | [-0.0088, 0.0518] | 11/9 | paired bootstrap | 0.296 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | table | hires | 60 | 0.8525 | 0.8529 | +0.0004 | [-0.0, 0.0012] | 2/1 | paired bootstrap | 0.285 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | table | selfcheck | 60 | 0.8525 | 0.8474 | -0.0051 | [-0.0342, 0.0262] | 11/15 | paired bootstrap | 0.676 | exploratory | 1.0 | not significant |
| ollama:qwen3.8:27b@desktop | table | upscale | 60 | 0.8525 | 0.8524 | -0.0001 | [-0.01, 0.0095] | 18/9 | paired bootstrap | 0.944 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | chart_qa | expert | 200 | 0.85 | 0.84 | -0.0100 | [-0.04, 0.015] | 3/5 | exact McNemar | 0.7266 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | chart_qa | hires | 200 | 0.85 | 0.85 | +0.0000 | [0.0, 0.0] | 0/0 | exact McNemar | 1.0 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | chart_qa | selfcheck | 200 | 0.85 | 0.91 | +0.0600 | [0.015, 0.105] | 17/5 | exact McNemar | 0.0169 | exploratory | 0.9464 | not significant |
| openai:qwen3vl32b@desktop | chart_qa | upscale | 200 | 0.85 | 0.895 | +0.0450 | [0.01, 0.08] | 11/2 | exact McNemar | 0.0225 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | chart_qa_confirm | tuned | 2022 | 0.864 | 0.8828 | +0.0188 | [0.0059, 0.0321] | 113/75 | exact McNemar | 0.0068 | confirmatory | 0.0136 | better |
| openai:qwen3vl32b@desktop | chart_qa_confirm2 | selfcheck | 1322 | 0.82 | 0.8449 | +0.0250 | [0.0091, 0.0416] | 78/45 | exact McNemar | 0.0037 | supporting_v2 | 0.0112 | better |
| openai:qwen3vl32b@desktop | chart_qa_confirm2 | upscale | 1322 | 0.82 | 0.8351 | +0.0151 | [0.0023, 0.0272] | 45/25 | exact McNemar | 0.0225 | supporting_v2 | 0.0411 | better |
| openai:qwen3vl32b@desktop | chart_qa_confirm2 | vote3 | 1322 | 0.82 | 0.8457 | +0.0257 | [0.0136, 0.0371] | 49/15 | exact McNemar | 0.0 | confirmatory_v2 | 0.0001 | better |
| openai:qwen3vl32b@desktop | chart_qa_dev2 | readfirst | 586 | 0.8379 | 0.8567 | +0.0188 | [-0.0051, 0.0444] | 34/23 | exact McNemar | 0.1849 | exploratory_v2 | 0.5546 | not significant |
| openai:qwen3vl32b@desktop | chart_qa_dev2 | selfcheck | 586 | 0.8379 | 0.8652 | +0.0273 | [0.0051, 0.0495] | 30/14 | exact McNemar | 0.0226 | exploratory_v2 | 0.1131 | not significant |
| openai:qwen3vl32b@desktop | chart_qa_dev2 | upscale | 586 | 0.8379 | 0.8584 | +0.0205 | [0.0017, 0.0392] | 21/9 | exact McNemar | 0.0428 | exploratory_v2 | 0.1711 | not significant |
| openai:qwen3vl32b@desktop | chart_qa_dev2 | vote3 | 586 | 0.8379 | 0.8669 | +0.0290 | [0.0137, 0.0461] | 19/2 | exact McNemar | 0.0002 | exploratory_v2 | 0.0018 | better |
| openai:qwen3vl32b@desktop | chart_table | expert | 60 | 0.9009 | 0.8931 | -0.0078 | [-0.0486, 0.0336] | 1/4 | paired bootstrap | 0.669 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | chart_table | hires | 60 | 0.9009 | 0.9009 | +0.0000 | [0.0, 0.0] | 0/0 | paired bootstrap | 1.0 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | chart_table | selfcheck | 60 | 0.9009 | 0.9017 | +0.0008 | [-0.0492, 0.0508] | 2/2 | paired bootstrap | 0.899 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | chart_table | upscale | 60 | 0.9009 | 0.9021 | +0.0012 | [-0.0487, 0.0499] | 3/2 | paired bootstrap | 0.888 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | page_text | layoutmask | 40 | 0.8094 | 0.8951 | +0.0858 | [0.0403, 0.1353] | 20/16 | paired bootstrap | 0.0 | exploratory_v2 | 0.0 | better |
| openai:qwen3vl32b@desktop | page_text_confirm2 | layoutmask | 80 | 0.8138 | 0.8805 | +0.0668 | [0.033, 0.101] | 37/36 | paired bootstrap | 0.0 | confirmatory_v2 | 0.0 | better |
| openai:qwen3vl32b@desktop | table | expert | 60 | 0.8212 | 0.8486 | +0.0274 | [0.0017, 0.0594] | 10/11 | paired bootstrap | 0.034 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | table | hires | 60 | 0.8212 | 0.8213 | +0.0001 | [-0.0, 0.0004] | 2/1 | paired bootstrap | 0.51 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | table | selfcheck | 60 | 0.8212 | 0.8278 | +0.0067 | [-0.0197, 0.0353] | 15/15 | paired bootstrap | 0.654 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | table | upscale | 60 | 0.8212 | 0.8409 | +0.0197 | [-0.0019, 0.0444] | 15/12 | paired bootstrap | 0.075 | exploratory | 1.0 | not significant |
| openai:qwen3vl32b@desktop | table_confirm | tuned | 159 | 0.8508 | 0.8414 | -0.0094 | [-0.0295, 0.0099] | 24/33 | paired bootstrap | 0.323 | confirmatory | 0.323 | not significant |

## Reproducibility: the same model run on both machines (laptop minus desktop)

| model | task | variant | shared cases | same weights | identical answers | identical scores | desktop | laptop | difference [95% CI] | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| ollama:qwen2.5vl:7b | chart_qa | baseline | 200 | yes | 94.5% | 98.0% | 0.535 | 0.525 | -0.0100 [-0.03, 0.01] | reproduced |
| ollama:qwen2.5vl:7b | chart_qa | expert | 200 | yes | 91.5% | 96.0% | 0.445 | 0.475 | +0.0300 [0.005, 0.06] | sides disagree |
| ollama:qwen2.5vl:7b | chart_qa | selfcheck | 200 | yes | 64.5% | 94.0% | 0.8 | 0.79 | -0.0100 [-0.045, 0.025] | reproduced |
| ollama:qwen2.5vl:7b | chart_qa | upscale | 200 | yes | 93.0% | 97.5% | 0.49 | 0.475 | -0.0150 [-0.04, 0.005] | reproduced |
| ollama:qwen2.5vl:7b | chart_table | baseline | 60 | yes | 66.7% | 86.7% | 0.7153 | 0.6497 | -0.0656 [-0.1444, 0.0067] | reproduced |
| ollama:qwen2.5vl:7b | chart_table | expert | 60 | yes | 60.0% | 93.3% | 0.5328 | 0.5406 | +0.0079 [-0.0463, 0.0625] | reproduced |
| ollama:qwen2.5vl:7b | chart_table | selfcheck | 60 | yes | 38.3% | 73.3% | 0.7078 | 0.6256 | -0.0821 [-0.1886, 0.0193] | reproduced |
| ollama:qwen2.5vl:7b | chart_table | upscale | 60 | yes | 55.0% | 75.0% | 0.7837 | 0.6359 | -0.1477 [-0.2549, -0.0593] | sides disagree |
| ollama:qwen2.5vl:7b | ocr_crop | baseline | 50 | yes | 90.0% | 96.0% | 0.0243 | 0.0253 | +0.0011 [0.0, 0.0034] | reproduced |
| ollama:qwen2.5vl:7b | table | baseline | 60 | yes | 80.0% | 83.3% | 0.724 | 0.7239 | -0.0000 [-0.0103, 0.0108] | reproduced |
| ollama:qwen2.5vl:7b | table | expert | 60 | yes | 71.7% | 75.0% | 0.7476 | 0.7574 | +0.0098 [-0.0018, 0.0239] | reproduced |
| ollama:qwen2.5vl:7b | table | selfcheck | 60 | yes | 76.7% | 83.3% | 0.7524 | 0.7491 | -0.0033 [-0.0091, 0.0014] | reproduced |
| ollama:qwen2.5vl:7b | table | upscale | 60 | yes | 88.3% | 88.3% | 0.7338 | 0.7284 | -0.0054 [-0.0193, 0.0028] | reproduced |
| ollama:qwen3-vl:8b-instruct | chart_qa | baseline | 200 | NO | 93.0% | 97.5% | 0.78 | 0.795 | +0.0150 [-0.005, 0.035] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | chart_qa | expert | 200 | NO | 92.0% | 96.0% | 0.76 | 0.75 | -0.0100 [-0.035, 0.015] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | chart_qa | selfcheck | 200 | NO | 51.0% | 95.5% | 0.325 | 0.36 | +0.0350 [0.01, 0.065] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | chart_qa | upscale | 200 | NO | 96.0% | 98.5% | 0.795 | 0.8 | +0.0050 [-0.01, 0.02] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | chart_table | baseline | 60 | NO | 70.0% | 88.3% | 0.4827 | 0.4179 | -0.0648 [-0.1463, 0.0037] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | chart_table | expert | 60 | NO | 75.0% | 98.3% | 0.9154 | 0.8999 | -0.0155 [-0.0466, 0.0] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | chart_table | selfcheck | 60 | NO | 83.3% | 98.3% | 0.9302 | 0.9296 | -0.0006 [-0.0017, 0.0] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | chart_table | upscale | 60 | NO | 65.0% | 83.3% | 0.6429 | 0.6304 | -0.0125 [-0.1125, 0.0833] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | ocr_crop | baseline | 50 | NO | 96.0% | 96.0% | 0.0123 | 0.0124 | +0.0001 [0.0, 0.0003] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | table | baseline | 60 | NO | 80.0% | 83.3% | 0.8186 | 0.8177 | -0.0009 [-0.0025, 0.0004] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | table | expert | 60 | NO | 80.0% | 86.7% | 0.8218 | 0.8285 | +0.0068 [-0.0017, 0.0221] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | table | selfcheck | 60 | NO | 78.3% | 91.7% | 0.8181 | 0.8231 | +0.0049 [-0.012, 0.0245] | different weights: not a reproduction test |
| ollama:qwen3-vl:8b-instruct | table | upscale | 60 | NO | 88.3% | 91.7% | 0.8321 | 0.8312 | -0.0009 [-0.0026, 0.0] | different weights: not a reproduction test |
