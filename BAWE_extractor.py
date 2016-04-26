# coding: utf-8
__author__ = 'lizaku55'

import os, lxml.html, json
from nltk.tokenize import RegexpTokenizer
tokenizer = RegexpTokenizer('\w+|\$[\d\.]+|\S+')
from math import log10, sqrt
import nltk.collocations
bigram_measures = nltk.collocations.BigramAssocMeasures()
from collections import OrderedDict

PATH_BAWE = '/home/lizaku55/Документы/BAWE'
punct = '"\'()/<>{}:;-'

result = OrderedDict()
corp = []
all_bigrams = set()

def extract_cats():
    categories = {}
    path = os.path.join(PATH_BAWE, 'CORPUS_UTF-8')
    for fname in os.listdir(path):
        if not fname.endswith('xml'):
            continue
        # print(fname)
        with open(os.path.join(path, fname), 'r', encoding='utf-8') as f:
            html = f.read().replace('<?xml version="1.0" encoding="UTF-8"?>', '')
        root = lxml.html.fromstring(html)
        category = root.xpath('//p[@n="discipline"]/text()')[0]
        try:
            categories[category].append(fname.split('.')[0])
        except KeyError:
            categories[category] = [fname.split('.')[0]]
    return categories


def make_corpora(categories):
    path = os.path.join(PATH_BAWE, 'CORPUS_TXT')
    for cat in categories:
        with open(cat + '.txt', 'w', encoding='utf-8') as f:
            for fname in categories[cat]:
                text = open(os.path.join(path, fname + '.txt'), 'r', encoding='utf-8').read()
                f.write(text + '\n')

def make_tables():
    path = os.path.join(os.getcwd(), 'corpora')
    corpora = os.listdir(path)
    dic_all = {}
    for corpus in corpora:
        print(corpus)
        with open(os.path.join(path, corpus), 'r', encoding='utf-8') as f:
            text = f.read()
            for i in punct:
                text = text.replace(i, ' ')
            tokens = tokenizer.tokenize(text)
            dic_freq = {}
            dic_bigr = {}
            for token in range(0, len(tokens) - 1):
                if tokens[token] not in punct:
                    try:
                        dic_freq[tokens[token]] += 1
                    except KeyError:
                        dic_freq[tokens[token]] = 1
                    if tokens[token + 1] not in punct:
                        try:
                            dic_bigr[' '.join((tokens[token], tokens[token + 1]))] += 1
                        except KeyError:
                            dic_bigr[' '.join((tokens[token], tokens[token + 1]))] = 1
            dic_all[corpus] = [len(tokens), dic_freq, dic_bigr]
    with open('frequencies.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(dic_all, ensure_ascii=False))
    return dic_all


def pmi(freqs):
    f = open('pmi_realec.csv', 'w', encoding='utf-8')
    for corpus in freqs:
        corp.append(corpus.split('.')[0])
        result[corpus.split('.')[0]] = {}
        print(1, corpus)
        # with open(os.path.join('pmi', corpus + '.csv'), 'w', encoding='utf-8') as f:
        N, unigrams, bigrams = freqs[corpus]
        bigrs = {}
        for bigr in bigrams:
            try:
                npmi = log10((bigrams[bigr] / (N - 1)) / (
                (unigrams[bigr.split(' ')[0]] / N) * (unigrams[bigr.split(' ')[1]] / N)))
                bigrs[bigr] = '%.5f' % npmi
            except:
                continue
        for i in sorted(bigrs, key=lambda x: bigrs[x], reverse=True)[:1000]:
            result[corpus.split('.')[0]][i] = bigrs[i]
    f.write('bigram\t' + '\t'.join(corp) + '\n')
    for corpus in result:
        for k in result[corpus].keys():
            all_bigrams.add(k)
    for b in all_bigrams:
        line = b
        for c in corp:
            try:
                line += '\t' + result[c][b]
            except KeyError:
                line += '\t' + '0'
        f.write(line + '\n')
    f.close()


def tscore(freqs):
    f = open('tscore_realec.csv', 'w', encoding='utf-8')
    for corpus in freqs:
        corp.append(corpus.split('.')[0])
        result[corpus.split('.')[0]] = {}
        print(1, corpus)
        # with open(os.path.join('pmi', corpus + '.csv'), 'w', encoding='utf-8') as f:
        N, unigrams, bigrams = freqs[corpus]
        bigrs = {}
        for bigr in bigrams:
            try:
                t = (bigrams[bigr] / N - (unigrams[bigr.split(' ')[0]] / N) * (unigrams[bigr.split(' ')[1]] / N) / sqrt(
                    bigrams[bigr] / N / N))
                bigrs[bigr] = '%.5f' % t
            except:
                continue
        for i in sorted(bigrs, key=lambda x: bigrs[x])[:1000]:
            result[corpus.split('.')[0]][i] = bigrs[i]
    f.write('bigram\t' + '\t'.join(corp) + '\n')
    for corpus in result:
        for k in result[corpus].keys():
            all_bigrams.add(k)
    for b in all_bigrams:
        line = b
        for c in corp:
            try:
                line += '\t' + result[c][b]
            except KeyError:
                line += '\t' + '0'
        f.write(line + '\n')
    f.close()


def logl(freqs):
    f = open('loglikelihood_realec.csv', 'w', encoding='utf-8')
    for corpus in freqs:
        corp.append(corpus.split('.')[0])
        result[corpus.split('.')[0]] = {}
        print(1, corpus)
        # with open(os.path.join('pmi', corpus + '.csv'), 'w', encoding='utf-8') as f:
        N, unigrams, bigrams = freqs[corpus]
        bigrs = {}
        for bigr in bigrams:
            try:
                l = bigram_measures.likelihood_ratio(bigrams[bigr], (unigrams[bigr.split(' ')[0]],
                                                                     unigrams[bigr.split(' ')[1]]), N)
                bigrs[bigr]= '%.5f' % l
            except:
                continue
        for i in sorted(bigrs, key=lambda x: bigrs[x])[:1000]:
            result[corpus.split('.')[0]][i] = bigrs[i]
    f.write('bigram\t' + '\t'.join(corp) + '\n')
    for corpus in result:
        for k in result[corpus].keys():
            all_bigrams.add(k)
    for b in all_bigrams:
        line = b
        for c in corp:
            try:
                line += '\t' + result[c][b]
            except KeyError:
                line += '\t' + '0'
        f.write(line + '\n')
    f.close()


if __name__ == '__main__':
    # dic[bigr] = {t-score: {Ling: 34, Law: 76}, pmi: {Ling: 345, Law: 3425}}
    #categories = extract_cats()
    #make_corpora(categories)
    #make_tables()
    freqs = json.loads(open('frequencies.json').read())
    logl(freqs)
    #tscore(freqs)
    #pmi(freqs)
    #with open('metrics.json', 'w', encoding='utf-8') as f:
    #    f.write(json.dumps(result, ensure_ascii=False))