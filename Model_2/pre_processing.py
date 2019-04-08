import pickle
import random

import gensim
import nltk
import spacy
from nltk.corpus import stopwords

# Reading stop-words
stop_words = set(stopwords.words('english'))
# Loading spacy's model
nlp = spacy.load('en')
# Punctuation's list
punctuation = "[!”#$%&’()*+,-./:;<=>?@[\]^_`{|}~]:0123456789"
# Negation words
neg_words = ['not', 'no', 'nothing', 'never']


def tuple_to_list(tuples):
    result = []

    for tuple in tuples:
        object = [tuple[0], tuple[1]]
        result.append(object)

    return result


def rare_features(dataset, minimum_tf):
    vocabulary = {}

    for text in dataset:

        tokens = []
        doc = nlp(text)
        for word in doc:
            tokens.append(word.lemma_)

        for word in tokens:
            if word not in vocabulary:
                vocabulary[word] = 1
            else:
                aux = vocabulary[word]
                aux += 1
                vocabulary[word] = aux
    result = []

    for word in vocabulary:
        if vocabulary[word] < minimum_tf:
            result.append(word)

    return result


def negation_processing(text):
    negable = ['NN', 'JJ', 'VB']
    size = len(text)

    text = tuple_to_list(text)

    for i in range(size):
        if text[i][0] in neg_words:
            j = i + 1
            while j < size:
                if text[j][1] in negable:
                    word_reverse = text[j][0] + '_' + 'not'
                    text[j][0] = word_reverse
                    break
                j += 1
    return text


def to_process(docs, pos, minimum_tf):
    # Loading rare rare_features
    rare = rare_features(docs, minimum_tf)

    new_docs = []

    for text in docs:

        # Tokenizing & lemmatization
        tokens = []
        doc = nlp(text)
        for word in doc:
            if word.lemma_ != '-PRON-':
                tokens.append(word.lemma_)

        # POS filter: only adverbs, adjectives and nouns
        pos_tags = nltk.pos_tag(tokens)
        pos_tags = negation_processing(pos_tags)

        # Removing stop words & punctuation & rare features
        tokens_filtered = []
        for word in pos_tags:
            if word[0] not in stop_words and word[0] not in punctuation and word[0] not in rare:
                tokens_filtered.append(word)

        pos_tags = tokens_filtered
        result_pos = []

        if pos == '3':
            for word in pos_tags:
                if word[1] == 'NN' or word[1] == 'NNS' or word[1] == 'NNP' or \
                        word[1] == 'NNPS':
                    result_pos.append(word[0])

        elif pos == '1':
            for word in pos_tags:
                if word[1] == 'JJ' or word[1] == 'JJR' or word[1] == 'JJS':
                    result_pos.append(word[0])

        elif pos == '5':
            for word in pos_tags:
                if word[1] == 'JJ' or word[1] == 'JJR' or word[1] == 'JJS' or word[1] == 'RB' or \
                        word[1] == 'RB' or word[1] == 'RBR' or word[1] == 'RBS':
                    result_pos.append(word[0])

        elif pos == '2':
            for word in pos_tags:
                if word[1] == 'RB' or word[1] == 'RBR' or word[1] == 'RBS':
                    result_pos.append(word[0])

        elif pos == '4':
            for word in pos_tags:
                if word[1] == 'VB' or word[1] == 'VBD' or word[1] == 'VBG' or \
                        word[1] == 'VBN' or word[1] == 'VBP' or word[1] == 'VBZ':
                    result_pos.append(word[0])
        elif pos == '6':
            for word in pos_tags:
                if word[1] == 'JJ' or word[1] == 'JJR' or word[1] == 'JJS' or word[1] == 'VB' or \
                        word[1] == 'NN' or word[1] == 'NNS' \
                        or word[1] == 'NNP' or word[1] == 'NNPS':
                    result_pos.append(word[0])
        else:
            result_pos = tokens_filtered

        new_docs.append(result_pos)

    return new_docs

def gen_data():
    with open('Datasets/dataset_books', 'rb') as fp:
        data_source_a = pickle.load(fp)
    with open('Datasets/dataset_kitchen', 'rb') as fp:
        data_source_b = pickle.load(fp)
    with open('Datasets/dataset_electronics', 'rb') as fp:
        data_source_c = pickle.load(fp)

    def suffling(data):
        docs = data.docs
        labels = data.labels

        c = list(zip(docs, labels))

        random.shuffle(c)

        docs, labels = zip(*c)

        data.docs = docs
        data.labels = labels

        return data

    data_source_a.docs = to_process(data_source_a.docs, '6')
    data_source_b.docs = to_process(data_source_b.docs, '6')
    data_source_c.docs = to_process(data_source_c.docs, '6')

    data_source_a = suffling(data_source_a)
    data_source_b = suffling(data_source_b)
    data_source_c = suffling(data_source_c)

    print(data_source_a.docs)

    with open('dataset_books', 'wb') as fp:
        pickle.dump(data_source_a, fp)
    with open('dataset_kitchen', 'wb') as fp:
        pickle.dump(data_source_b, fp)
    with open('dataset_electronics', 'wb') as fp:
        pickle.dump(data_source_c, fp)
