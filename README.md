# CONVEX

CONVEX is an unsupervised method that can answer incomplete questions over knowledge graphs (Wikidata in our case) by maintaining conversation context using entities and predicates seen so far and automatically inferring missing or ambiguous pieces for follow-up questions. The core of our method is a graph exploration algorithm that judiciously expands a frontier to find candidate answers for the current question. For details, please refer to the paper.

The website of our work (including a demo) is available here:  https://convex.mpi-inf.mpg.de/
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

(If there are any issues installing hdt, please check out issue #5).

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

# Citation
Please cite our CIKM 2019 paper if you use CONVEX in your work:
```shell
@inproceedings{christmann2019look,
 author = {Christmann, Philipp and Saha Roy, Rishiraj and Abujabal, Abdalghani and Singh, Jyotsna and Weikum, Gerhard},
 title = {Look Before You Hop\&\#58; Conversational Question Answering over Knowledge Graphs Using Judicious Context Expansion},
 booktitle = {Proceedings of the 28th ACM International Conference on Information and Knowledge Management},
 series = {CIKM '19},
 year = {2019},
 isbn = {978-1-4503-6976-3},
 location = {Beijing, China},
 pages = {729--738},
 numpages = {10},
 url = {http://doi.acm.org/10.1145/3357384.3358016},
 doi = {10.1145/3357384.3358016},
 acmid = {3358016},
 publisher = {ACM},
 address = {New York, NY, USA},
 keywords = {conversations, knowledge graphs, question answering},
} 
```

# License
The CONVEX project by Philipp Christmann, Rishiraj Saha Roy and Gerhard Weikum is licensed under MIT license.
