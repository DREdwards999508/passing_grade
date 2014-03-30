'''
3/30/2014
Daniel Edwards, Diego Lanao, Will Stalcup, Will Theuer
Hackathon ITPIR Database Challenge
'''
from collections import deque, defaultdict
import MySQLdb
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, make_response
from wtforms import Form, BooleanField, StringField, SelectField, TextAreaField, PasswordField, TextField, validators

app = Flask(__name__)
app.config.from_object(__name__)

app.config.from_envvar('FLASKR_SETTINGS', silent=True)
            
def associationPath(name1, name2):
    visited = []
    asslist = deque()
    asslist.append(name1)
    visited.append(name1)
    parent = {}
    for i in fields:
        for j in i:
            parent[j] = None
    while name2 not in asslist:
        currentParent = asslist.popleft()
        for i in associations[currentParent]:
            if i not in visited:
                if parent[i] == None:
                    parent[i] = currentParent
                asslist.append(i)
                visited.append(i)
    pathlist = []
    temparent = parent[name2]
    
    temp = name2
    while temp != name1:
        pathlist.append(temp)
        temp = temparent
        temparent = parent[temparent]
    
    pathlist.append(temp)
    
    pathlist.reverse()
    return pathlist

def findTable(field1, field2):
    for i in range(len(fields)):
        if field1 in fields[i] and field2 in fields[i]:
            return tables[i]
    raise KeyError
    
def findAssociations(name1, name2, value):
    myList = associationPath(name1, name2)
    index = 0
    result = [value]
    while index < len(myList)-1:
        tempTable = findTable(myList[index], myList[index+1])
        tabnum = 0
        for i in range(len(tables)):
            if tables[i] == tempTable:
                tabnum = i
        temp = result
        result = association(tabnum, myList[index], myList[index+1], temp)
        index+=1
    return result

def filterDown(index, field2, dataList, field, value, field3):
    results = []
    fieldNum3 = None
    for i in range(len(fields[index])):
        if fields[index][i] == field3:
            fieldNum3 = i
    fieldNum2 = None
    for i in range(len(fields[index])):
        if fields[index][i] == field2:
            fieldNum2 = i
    fieldNum = None
    for i in range(len(fields[index])):
        if fields[index][i] == field:
            fieldNum = i
    for i in data[index]:
        if i[fieldNum2] in dataList and i[fieldNum]==value:
            results.append(i[fieldNum3])
    return results

def tally(dataList):
    tally = defaultdict(int)
    for i in dataList:
        tally[i]+=1
    return tally

def getResponse(table, num, field1index, field2index):
    results = []
    for i in data[table]:
        if i[field1index] == num:
            results.append(i[field2index]) 
    return results

'''def javaScriptOutputBar(surveyResults, questionnum):
    values = surveyResults.values()
    keys = surveyResults.keys()
    myString = """
<section>
<div id="graphDiv1"></div>
    <br />
    <div id="graphDiv2"></div>
    <!--[if IE]><script src="excanvas.js"></script><![endif]-->
    <script src="html5-canvas-bar-graph.js"></script>
    <script>(function () {

        function createCanvas(divName) {

            var div = document.getElementById(divName);
            var canvas = document.createElement('canvas');
            div.appendChild(canvas);
            if (typeof G_vmlCanvasManager != 'undefined') {
                canvas = G_vmlCanvasManager.initElement(canvas);
            }    
            var ctx = canvas.getContext("2d");
            return ctx;
        }

        var ctx = createCanvas("graphDiv1");

        var graph = new BarGraph(ctx);
        graph.maxValue = 200;
        graph.margin = 2;
        graph.colors = ["#00D078","#D95B43","#C02942","#0000AA","#AA00AA", "#00AA00","#00AAAA"];
        setInterval(function () {
            graph.update([]);
        }, 1000);

    }());</script></section>"""
    return myString'''

def javaScriptOutputPie(surveyResults, questionnum):
    values = surveyResults.values()
    keys = surveyResults.keys()
    myString = """
   
<section>
<div>
<canvas id="canvas" width="500" height="500">
This text is displayed if your browser does not support HTML5 Canvas.
</canvas>
</div>

<script type="text/javascript">

var myColor = ["#00D078","#D95B43","#C02942","#0000AA","#AA00AA", "#00AA00","#00AAAA"];
var myData = ["""
    for i in range(len(values)-1):
        myString= myString+str(values[i])+", "
    myString = myString+str(values[-1])
    myString = myString+"""];
    
var myLabels = ["""
    for i in range(len(keys)-1):
        myString = myString+"\""+answers[keys[i]]+"\""+', '
    myString = myString+"\""+answers[keys[-1]]+"\""
    myString = myString+"""];



function plotData() {
var canvas;
var ctx;
var lastend = 0;
var myTotal = """
    myString = myString+str(sum(values))
    myString = myString+""";

canvas = document.getElementById("canvas");
ctx = canvas.getContext("2d");
ctx.clearRect(0, 0, canvas.width, canvas.height);
for (var i = 0; i < myData.length; i++) {
ctx.fillStyle = myColor[i];
ctx.beginPath();
ctx.moveTo(200,170);
ctx.arc(200,170,170,lastend,lastend+
  (Math.PI*2*(myData[i]/myTotal)),false);
ctx.font = "12px Arial";
ctx.fillText(myLabels[i]+": "+myData[i], 10,365+20*i);
ctx.lineTo(200,170);
ctx.fill();
lastend += Math.PI*2*(myData[i]/myTotal);
}
}

plotData();

</script>
</section>  """        
    return myString

def association(tablekey, field1, field2, condition):
    fieldnum1 = 0
    fieldnum2 = 0
    result = []
    for i in range(len(fields[tablekey])):
        if fields[tablekey][i] == field1:
            fieldnum1 = i
        elif fields[tablekey][i] == field2:
            fieldnum2 = i
    for i in data[tablekey]:
        if i[fieldnum1] in condition:
            result.append(i)
    finalresult = []
    for i in result:
        finalresult.append(i[fieldnum2])
    return finalresult

def limitAnswers(goodAnswers, fullSet):
    newDict = {}
    for i in range(len(fullSet.keys())):
        if fullSet.keys()[i] in goodAnswers:
            newDict[fullSet.keys()[i]] = fullSet.values()[k]
    return newDict

def createStringsDict(a, b, c):
    s1 = []
    s2 = []
    for i in range(len(data[a])):
        s1.append(data[a][i][b])
        s2.append(data[a][i][c])
    d = {}
    for i in range(len(s1)):
        d[s1[i]] = s2[i]
    return d
    

db = MySQLdb.connect("localhost", "root", "clubby", "test")
c = db.cursor()
c.execute("SHOW TABLES")
    
#store all of the relevant data
tables = [i[0] for i in c.fetchall()]
data = []
fields = []
for i in tables:
    c.execute("SELECT * FROM test." + i + ";")
    data.append(c.fetchall())
    fields.append([i[0] for i in c.description])
    
#fix naming conventions
for i in range(len(tables)):
    if tables[i][-1] == "s":
        tables[i] = tables[i][0:-1]
   
for i in range(len(fields)):
    if fields[i][0] == "id":
        if tables[i][0:14] == "sample_survey_":
            fields[i][0] = tables[i][14:] + "_id"
        else:
            fields[i][0] = tables[i][7:] + "_id"  
    
answers = createStringsDict(2, 0, 4)
questions = createStringsDict(11, 0, 1)

#store questions with answers
answersToQuestions = {}
for i in range(len(data[2])):
    try:
        answersToQuestions[data[2][i][2]].append(data[2][i][0])
    except KeyError:
        answersToQuestions[data[2][i][2]] = [data[2][i][0]]

#dictionary for associations
associations = {}
for i in fields:
    for j in i:
        try:
            for k in i:
                if k != j:
                    associations[j].add(k)
        except KeyError:
            associations[j] = set()
            for k in i:
                if k != j:
                    associations[j].add(k)
                    
                    
filterChoice = ''
questionChoice = ''
answerChoice = []

questionChoices = []
for item in questions.keys():
    questionChoices.append((item, questions[item]))
answerChoices = [('0', 'Choose a question to see answers')]
filterChoices = [('m', 'men'), ('f', 'women')]
graphChoices = [('1', 'bar'), ('2', 'pie')]
myList = []

@app.route('/select', methods = ['GET', 'POST']) 
def CommentSelect():
    #multiselect = request.form.getlist("mymultiselect")
    return render_template('commentform.html', 
        questionChoices = questionChoices, answerChoices = answerChoices,
        filterChoices = filterChoices, graphChoices = graphChoices)


class Question(Form):
    Question = SelectField('Questions', choices = questionChoices)

@app.route('/selectQuestion', methods = ['POST'])
def selectQuestion():
    form = Question(request.form)
    myList = request.form.getlist('mymultiselect')
    questionChoice = myList[0]
    answerChoices = []
    for i in answersToQuestions[int(questionChoice)]:
        answerChoices.append((i, answers[i]))
    answerChoices.append((int(questionChoice),int(questionChoice)))
    return render_template('commentform.html', questionChoices = questionChoices,
        answerChoices = answerChoices, filterChoices = filterChoices,
        graphChoices = graphChoices)

class Answer(Form):
    Answer = SelectField('Answers', choices = answerChoices)

@app.route('/selectAnswer', methods = ['POST'])  
def selectAnswer():
    form = Answer(request.form)
    myList = request.form.getlist('mymultiselects')
    answerChoice = myList
    return render_template('commentform.html', questionChoices = questionChoices,
        answerChoices = answerChoices, filterChoices = filterChoices,
        graphChoices = graphChoices)
    
class Filter(Form):
    Filter = SelectField('Filters', choices = filterChoices)
    
@app.route('/selectFilter', methods = ['POST'])    
def selectFilter():
    form = Filter(request.form)
    myList = request.form.get('mymultiselectz')
    filterChoice = myList[0] #m/f
    return render_template('commentform.html', questionChoices = questionChoices,
        answerChoices = answerChoices, filterChoices = filterChoices,
        graphChoices = graphChoices)
    

class GraphType(Form):
    GraphType = SelectField('GraphTypes', choices = graphChoices)

@app.route('/graphDisplay', methods = ['POST'])
def graphDisplay():
    form = GraphType(request.form)
    myList = request.form.get('mymultiselex')
    graphChoice = myList[0]
    #SurveyResults = generateResults(request.cookies.get('filter'), request.cookies.get('question'), request.cookies.get('answer'))
    jscript = '''<section>
<div>
<canvas id="canvas" width="500" height="500">
This text is displayed if your browser does not support HTML5 Canvas.
</canvas>
</div>

<script type="text/javascript">

var myColor = ["#00D078","#D95B43","#C02942","#0000AA","#AA00AA", "#00AA00","#00AAAA"];
var myData = [11, 141, 48, 17];
    
var myLabels = ["Syria will comply by June 30, 2014", "Syria will not comply by June 30, 2014, but it ultimately will comply with the agreement", "Syria will not comply with the agreement", "Don't know"];



function plotData() {
var canvas;
var ctx;
var lastend = 0;
var myTotal = 217;

canvas = document.getElementById("canvas");
ctx = canvas.getContext("2d");
ctx.clearRect(0, 0, canvas.width, canvas.height);
for (var i = 0; i < myData.length; i++) {
ctx.fillStyle = myColor[i];
ctx.beginPath();
ctx.moveTo(200,170);
ctx.arc(200,170,170,lastend,lastend+
  (Math.PI*2*(myData[i]/myTotal)),false);
ctx.font = "12px Arial";
ctx.fillText(myLabels[i]+": "+myData[i], 10,365+20*i);
ctx.lineTo(200,170);
ctx.fill();
lastend += Math.PI*2*(myData[i]/myTotal);
}
}

plotData();

</script>
</section> '''
    
    
    return render_template('graphDisplay.html', jscript = jscript)
    

def generateResults(theList, qNumber, ansList):
    if theList:
        a = findAssociations('gender', 'response_id', [theList])
        b = filterDown(12, 'response_id', a, 'question_id', qNumber, 'answer_id')
    else:
        b = getResponse(12, qNumber, 1, 2)
    c = tally(b)
   # d = limitAnswers(ansList, c)
    return javaScriptOutputPie(d, qNumber)

if __name__ == '__main__':
    app.run()
    
