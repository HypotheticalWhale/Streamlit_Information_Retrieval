# CZ4034 Information Retrieval Group10
Repo of **Crypto.io** - A *NFT-related* Information Retrieval Project  

## Data Collection
**'1_crawling' folder**
1. scrape_tweets.ipynb
2. explore_data.ipynb  

## Data Preprocessing
**'2_preprocesing' folder**
1. preprocess_tweets.ipynb
2. prepare_files.ipynb
3. preprocessing_experiments.ipynb  

## Data Augmentation
**'3_augmentation' folder**
1. augmentation_experiments.ipynb
2. augment_train.ipynb  

## Sentiment Analysis
**'4_classification" folder**
1. unsupervised_classifiers.ipynb
2. xgboost_classifier.ipynb
3. lightgbm_classifier.ipynb
4. knn_classifier.ipynb
5. svm_classifier.ipynb
6. decisiontree_classifier.ipynb
7. naivebayes_classifier.ipynb
8. majority_voting.ipynb
9. lstm_classifier.ipynb
10. bert_classifier.ipynb  

## User Interface
**'6_ui' folder**  
*How To Install Elasticsearch*
* download and unzip `elasticsearch-8.7.0`
* in `/config/elasticsearch.yml` change lines 98 and 103 to `false`
* in `/config/roles.yml` add  
```
admins:
  cluster:
    - all
  indices:
    - names:
        - "*"
      privileges:
        - all
devs:
  cluster:
    - manage
  indices:
    - names:
        - "*"
      privileges:
        - write
        - delete
        - create_index
```
* add `\bin` folder to PATH environment variable
* open Command Prompt, `elasticsearch`
* check `localhost:9200`  

*How To Configure Elasticsearch User*
* open Command Prompt, `elasticsearch-users useradd <username> -p <password>`
* in `/config/users_roles` add `admins:<username>`  

*How To Install Project Dependencies*
* `cd 5_ui`
* `python -m venv env` to create a Python virtual environment
* `env\Scripts\activate` to activate the Python virtual environment
* `pip install -r requirements.txt` 

*How To Run*
* open Command Prompt, `elasticsearch`
* from project directory, in `crypto.io.py` change line 8 to `es = Elasticsearch(['http://localhost:9200'], http_auth=('<username>', '<password>'))`
* from `pages\2_scrape.py` change line 35 to `es = Elasticsearch(['http://localhost:9200'], http_auth=('<username>', '<password>'))`
* from project directory, open Command Prompt, `cd 5_ui`
* `env\Scripts\activate`
* `streamlit run crypto.io.py`
* `deactivate` to deactivate the Python virtual environment  

__TODO__
* remove dummy pages `hello.py` and `1_plot.py`
* integrate with indexing
* update `requirements.txt`
* move final_data.csv to datasets folder or create an assets folder to store with model and vectorizer  

## Datasets
**'datasets' folder**
1. label_dataset_final.csv
2. full_dataset_final.csv
3. train_aug.csv
4. test.csv