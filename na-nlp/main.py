from gensim.summarization import keywords
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from io import StringIO
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1
import re
import nltk

# nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import pickle
import numpy as np


class PdfConverter:

    def __init__(self, file_path):
        self.file_path = file_path

    # convert pdf file to a string which has space among words
    def convert_pdf_to_txt(self, pagenos):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'  # 'utf16','utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, laparams=laparams)
        fp = open(self.file_path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 1
        pagenos = range(pagenos, pagenos + maxpages)
        pagenos = set(pagenos)
        caching = True
        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                      check_extractable=True):
            interpreter.process_page(page)
        fp.close()
        device.close()
        str = retstr.getvalue()
        retstr.close()
        return str


def max_occurrences(nums):
    max_val = 0
    result = nums[0]
    for i in nums:
        occu = nums.count(i)
        if occu > max_val:
            max_val = occu
            result = i
    return result


def predict(filepath):
    reference = {0: 'Biology', 1: 'Chemistry', 2: 'Civics', 3: 'Cloud Computing', 4: 'History', 5: 'Machine Learning',
                 6: 'Networks', 7: 'Physics'}
    pdfConverter = PdfConverter(file_path=filepath)
    file = open(filepath, 'rb')
    parser = PDFParser(file)
    document = PDFDocument(parser)
    pages = resolve1(document.catalog['Pages'])['Count']
    data = []
    for i in range(0, pages + 1):
        page = pdfConverter.convert_pdf_to_txt(pagenos=i)
        if len(page.split(' ')) > 50:
            data.append(keywords(page, words=10, lemmatize=True).replace('\n', ' '))
    data = list(set(data))
    corpus = []
    for i in range(0, len(data)):
        data[i] = data[i].lower()
        data[i] = data[i].split()
        ps = PorterStemmer()
        all_stopwords = stopwords.words('english')
        data[i] = [ps.stem(word) for word in data[i] if not word in set(all_stopwords)]
        data[i] = ' '.join(data[i])
        corpus.append(data[i])
    corpus = list(set(corpus))
    clf = pickle.load(open("content/model.pkl", "rb"))
    corpus = np.array(corpus)
    corpus.reshape(1, -1)
    cv = pickle.load(open("content/cvector.pkl", "rb"))
    test = cv.transform(corpus).toarray()
    pred = clf.predict(test)
    domain = max_occurrences(list(pred))
    print(domain)
    print(reference[domain])
    return reference[domain]


predict('5. SAN - Information Storage and Management.pdf')
