import nltk
import numpy as np
import spacy
from nltk.corpus import sentiwordnet as swn
from nltk.corpus import stopwords, wordnet
from progress.bar import Bar

nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('sentiwordnet')
nltk.download('wordnet')
# python -m spacy download en
#
# adjectives, verbs, nouns, adverbs
#
# 0001 = adverbs
# 0010 = nouns
# 0011 = nouns, adverbs
# 0100 = verbs
# 0101 = verbs, adverbs
# 0110 = verbs, nouns
# 0111 = verbs, nouns, adverbs
# 1000 = adjectives
# 1001 = adjectives, adverbs
# 1010 = adjectives, nouns
# 1011 = adjectives, nouns, adverbs
# 1100 = adjectives, verbs
# 1101 = adjectives, verbs, adverbs
# 1110 = adjectives, verbs, nouns
# 1111 = adjectives, verbs, nouns, adverbs

# Reading stop-words
stop_words = set(stopwords.words('english'))
# Loading spacy's model
nlp = spacy.load('en_core_web_sm')
# Punctuation's list
punctuation = "[!”#$%&’()*+,-./:;<=>?@[\]^_`{|}~]:0123456789 "
# Negation words
neg_words = ['not', 'no', 'nothing', 'never']
# Resume pos
resume = {
    'JJ': 'a',
    'JJR': 'a',
    'JJS': 'a',
    'VB': 'v',
    'VBD': 'v',
    'VBG': 'v',
    'VBN': 'v',
    'VBP': 'v',
    'VBZ': 'v',
    'NN': 'n',
    'NNS': 'n',
    'NNP': 'n',
    'NNPS': 'n',
    'RB': 'r',
    'RBR': 'r',
    'RBS': 'r'
}

def resume_pos(param):
    if param in resume:
        return resume[param]
    return None


def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ,
                "N": wordnet.NOUN,
                "V": wordnet.VERB,
                "R": wordnet.ADV}

    return tag_dict.get(tag, wordnet.NOUN)


def tuple_to_list(tuples):
    result = []

    for tuple in tuples:
        object = [tuple[0], tuple[1]]
        result.append(object)

    return result


# input: list of strings (texts)
# output: list of strings (words)
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


# input: list of lists of strings (words)
# output: list of lists of strings
def negation_processing(text):
    negable = ['JJ', 'VB']
    size = len(text)

    text = tuple_to_list(text)

    for i in range(size):
        if text[i][0] in neg_words:
            j = i + 1
            while j < size:
                if text[j][1] in negable:
                    word_reverse = text[j][0] + '_not'
                    text[j][0] = word_reverse
                    break
                j += 1
    return text


def to_process(docs, pos, minimum_tf, label="Preprocessing"):
    bar = Bar(label, max=len(docs))
    new_docs = []
    pos_filter = []
    rare_vocab = rare_features(docs, minimum_tf)

    for i in range(4):
        if pos[i] == '1':
            if i == 0:
                pos_filter.append('a')
            elif i == 1:
                pos_filter.append('v')
            elif i == 2:
                pos_filter.append('n')
            else:
                pos_filter.append('r')

    for text in docs:
        # Tokenizing & lemmatization
        tokens = []
        doc = nlp(text)
        for word in doc:
            if word.lemma_ != '-PRON-':
                tokens.append(word.lemma_)

        # POS filter: only adverbs, adjectives and nouns
        pos_tags = nltk.pos_tag(tokens)

        # Removing stop words & punctuation & rare features
        tokens_filtered = []
        for word in pos_tags:
            if word[0] not in stop_words \
                    and word[0] not in punctuation \
                    and word[0].isalpha() \
                    and word[0] not in rare_vocab:
                aux = word[0].lower()
                tokens_filtered.append([aux, word[1]])

        pos_tags = tokens_filtered
        result_pos = []

        for word in pos_tags:
            aux = resume_pos(word[1])
            if aux is not None:
                if aux in pos_filter:
                    result_pos.append(word[0] + "_" + aux)

        new_docs.append(result_pos)
        bar.next()
    bar.finish()
    return new_docs


def get_vocabulary(dataset):
    vocab = {}

    for text in dataset:
        for word in text:
            if word not in vocab:
                vocab[word] = 0

    return vocab.keys()


def get_senti_representation(vocabulary, pos_form=False):
    vocab = []
    scores = []
    dicti = {}

    for item in vocabulary:

        word = ''
        pos = ''

        for i in range(len(item)):
            if item[i] == '_':
                word = item[:i]
                pos = item[i + 1:]

        if True:
            syns = list(swn.senti_synsets(word))
            if syns.__len__() > 0:
                pos_score = []
                neg_score = []
                obj_score = []
                for syn in syns:
                    if pos in syn.synset.name():
                        pos_score.append(syn.pos_score())
                        neg_score.append(syn.neg_score())
                        obj_score.append(syn.obj_score())

                if pos_score:
                    aux = [round(np.mean(pos_score), 3),
                           round(np.mean(neg_score), 3),
                           round(np.mean(obj_score), 3)]

                    if aux[0] > 0.2 or aux[1] > 0.2:
                        scores.append(aux)

                        if pos_form:
                            dicti[word + '_' + pos] = aux
                            vocab.append(word + '_' + pos)
                        else:
                            dicti[word] = aux
                            vocab.append(word)

    return vocab, scores, dicti


def sentiment_value(features, dicti):
    result = {}
    for feature in features:
        sent = []
        if feature.count("_") == 3:
            first = False

            for i in range(len(feature)):
                if feature[i] == '_' and not first:
                    first = True
                elif feature[i] == '_' and first:
                    aux1 = dicti[feature[:i]]
                    aux2 = dicti[feature[i + 1:]]
                    sent = [aux1[0] + aux2[0] / 2,
                            aux1[1] + aux2[1] / 2,
                            aux1[2] + aux2[2] / 2]
                    break
        else:
            sent = dicti[feature]

        result[feature] = sent
    return result


def get_idf(dataset, features):
    result = {}

    for feature in features:
        count = 0

        for text in dataset:
            if feature in text:
                count += 1

        result[feature] = count

    return result


def alsent(dataset, dicti, features):
    alsentvec = []
    sentivalues = sentiment_value(features, dicti)
    idfs = get_idf(dataset, features)

    for text in dataset:
        textvec = []
        for feature in features:
            if feature in text:
                tf = text.count(feature)
                idf = np.log(len(dataset)/idfs[feature])
                value = sentivalues[feature]

                if value[2] == 1:
                    sent = 0.1
                else:
                    sent = (value[0] - value[1]) + 1

                sentfidf = tf * idf * sent
                textvec.append(sentfidf)
            else:
                textvec.append(0)

        alsentvec.append(textvec)

    return np.array(alsentvec)
