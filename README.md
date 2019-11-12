# CONVEX

CONVEX is an unsupervised method that can answer incomplete questions over knowledge graphs (Wikidata in our case) by maintaining conversation context using entities and predicates seen so far and automatically inferring missing or ambiguous pieces for follow-up questions. The core of our method is a graph exploration algorithm that judiciously expands a frontier to find candidate answers for the current question. For details, please refer to the paper.

The website of our work is available here:  http://qa.mpi-inf.mpg.de/convex/  
A preprint of our corresponding CIKM'19 paper can be found here: https://arxiv.org/abs/1910.03262 

# Requirements

- Python 2.7 (Python 3 should also work) and the following modules:
  - Install all needed modules:
     ```shell
    pip install spacy requests hdt networkx
    ```
  - Install the spacy model: 
    ```shell
    python -m spacy download en_vectors_web_lg
    ```
- wget utility


# Run CONVEX on ConvQuestions 
***(with new train-dev-test split)***

1. Adjust the [settings file](settings.json) of the project.
  - Insert a valid token for the TagMe API (https://sobigdata.d4science.org/group/tagme).

2. Download the data folder and initialize the project.
```shell
  bash initialize.sh
```

3. Run **CONVEX** on the **ConvQuestions** benchmark. The results will be printed into a results.txt file.
```shell
  nohup python convex.py &
```
  
# Run CONVEX on another benchmark

1. Adjust the [settings file](settings.json) of the project. 
  - Insert a valid token for the TagMe API (https://sobigdata.d4science.org/group/tagme).
  - The 'conversations_path' attribute should refer to the path of the benchmark.

2. Download the data folder and initialize the project.
```shell
  bash initialize.sh
```

3. Run **CONVEX** on the given benchmark. The results will be printed into a results.txt file.
```shell
  nohup python convex.py &
```

# License
The CONVEX project by Philipp Christmann is licensed under MIT license.
