import nltk
#nltk.download('stopwords')
from pprint import pprint
from OuterQuestgen.Questgen import main
payload = {
            "input_text": "Java is a programming language and a platform. Java is a high level, robust, object-oriented and secure programming language.Java was developed by Sun Microsystems (which is now the subsidiary of Oracle) in the year 1995. James Gosling is known as the father of Java. Before Java, its name was Oak. Since Oak was already a registered company, so James Gosling and his team changed the Oak name to Java."
        }
qg = main.QGen()
output = qg.predict_mcq(payload)
pprint (output)
# output = qg.predict_shortq(payload)
# pprint (output)