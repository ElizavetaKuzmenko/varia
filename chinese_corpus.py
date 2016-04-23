# coding: utf-8

import re, os, lxml.html, time


# put the path to your file directory here
DIR_PATH = '/home/lizaku/PycharmProjects/varia/'
# put the path to the dictionary here
DICT_PATH = '/home/lizaku/PycharmProjects/varia/cedict_ts.u8'
# smart transription split
re_transcr = re.compile('([^\]]*\])')


def load_dict(path): # todo: save the dictionary in json and do not load it every time
    """
    transforms the dictionary file into a computationally feasible format
    :param path: the path to the dictionary
    :return: dictionary in the form {new_tok: (old_tok, transcr, transl) ...}
    """
    print('load dict...', time.asctime())
    cedict = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#'):
                continue
            old, new, transcr, transl = line.strip().split(' ', 3)
            m = re_transcr.search(transl)
            if m is not None:
                transcr += ' ' + m.group(1)
                transl = transl.replace(m.group(1), '')
                scr, sl = transcr.split(']', 1)
                transcr = scr + ']'
                transl = sl + transl
            if new not in cedict:
                cedict[new] = [(old, transcr, transl)]
            else:
                cedict[new].append((old, transcr, transl))
    return cedict


def load_corpus(path, cedict):
    """
    load and read all the files, transform them into the required form, write it down
    :param path: path to the dir with files
    :param cedict: Chinese dictionary
    """
    for f in os.listdir(path):
        if f.endswith('ml') and '_processed' not in f:
            new_f = open(f.rsplit('.', 1)[0] + '_processed.xml', 'w', encoding="utf-8")
            # here goes all the transformation
            sentences = make_xml(f, cedict)
            # write the transformed sentences one after another
            with open(f, 'r', encoding='utf-8') as orig:
                text = orig.read()
                print('replacing...', time.asctime())
                n = 0
                for sent in sentences:
                    text = text.replace(sent, sentences[sent])
                    n += 1
                new_f.write(text)
            new_f.close()


def extract_sentences(fname):
    """
    extract all Chinese sentences
    :param fname: path to the file
    :return: list of all Chinese sentences
    """
    with open(fname, 'r') as f:
        html = f.read().replace('<?xml version="1.0" encoding="utf-8"?>', '')
    root = lxml.html.fromstring(html)
    sentences = root.xpath(u'//se[contains(@lang, "zh")]/text()')
    return sentences


def make_xml(fname, cedict):
    """
    transform the sentences into RNC XML
    :param fname: path to the file
    :param cedict: Chinese dictionary
    :return: wrapped sentences
    """
    print('make xml...', time.asctime())
    sentences = extract_sentences(fname)
    sent_dict = {}
    for sent in range(len(sentences)):
        orig_sent = sentences[sent]
        # take a sentence and divide it into chunks
        fragments = sentences[sent].split('，')
        for fragment in fragments:
            # delete all the punctuation (keep in the original sentence)
            # todo: looks insane, change somehow
            fragment = fragment.replace('“', '').replace('”', '').replace('！', '').replace('。', '').replace('？', '')
            fragment = fragment.replace('：', '').replace('  ', '').replace('-', '').replace('‘', '').replace('、', '')
            fragment = fragment.replace('…', '').replace(' ', '').replace('ａ', '').replace('；', '').replace('\n', '')
            fragment = fragment.replace(' ', '')
            while len(fragment) > 0:
                # if we still have smth in the fragment...
                chunk = fragment
                # find the shortest dictionary entry
                # todo: there was some dynamic algorithm for this
                while chunk not in cedict and chunk != '':
                    chunk = chunk[:-1]
                # now we have the dictionary entry, extract its features and wrap into tags
                word_xml = '\n<w>'
                for elem in cedict[chunk]:
                    transcr = elem[1][1:-1]
                    # preprocess the translation
                    transl = elem[2].replace('/"', '/«').replace(' "', ' «').replace('" ', '» ').replace(' ', '_').replace('/', ', ').replace('_, ', '').strip().strip(',')
                    word_xml += '<ana lex="%s" transcr="%s" sem="%s"/>' % (chunk, transcr, transl)
                word_xml += chunk + '</w>'
                #print(word_xml)
                # change the original sentence
                # todo: cases with three characters in a row are not considered, the second one gets replaced
                sentences[sent] = re.sub('(?<!["_|])' + chunk + '(?!["<_\[])', word_xml.replace('=" ', '="'), sentences[sent])
                fragment = fragment[len(chunk):]
        sent_dict[orig_sent] = sentences[sent]
    return sent_dict

if __name__ == '__main__':
    cedict = load_dict(DICT_PATH)
    load_corpus(DIR_PATH, cedict)