from flask import Flask, request, redirect, render_template
from twilio.rest import TwilioRestClient
import twilio.twiml
import urllib2
import urllib
import re
app = Flask(__name__)

functionAliases = { 'der': 'DERfunction', 'derivative': 'DERfunction', 'derive': 'DERfunction', 'derivation': 'DERfunction', 'int': 'INTfunction', 'integrate': 'INTfunction', 'integral': 'INTfunction', 'integration': 'INTfunction', 'indefiniteint': 'INTfunction', 'indefiniteintegrate': 'INTfunction', 'indefiniteintegral': 'INTfunction', 'indefiniteintegration': 'INTfunction', 'ind': 'INDfunction', 'definiteint': 'INDfunction', 'definiteintegrate': 'INDfunction', 'definiteintegral': 'INDfunction', 'definiteintegration': 'INDfunction', 'inm': 'INMfunction', 'multivariableint': 'INMfunction', 'multivariableintegrate': 'INMfunction', 'multivariableintegral': 'INMfunction', 'multivariableintegration': 'INMfunction', 'multiint': 'INMfunction', 'multiintegrate': 'INMfunction', 'multiintegral': 'INMfunction', 'multiintegration': 'INMfunction', 'lim': 'LIMfunction', 'limit': 'LIMfunction', 'sum': 'SUMfunction', 'summation': 'SUMfunction', 'series': 'SUMfunction', 'seriessum': 'SUMfunction', 'sequencesum': 'SUMfunction', 'sigma': 'SUMfunction', 'mmu': 'MMUfunction', 'matrixmultiplication': 'MMUfunction', 'matrixmultiply': 'MMUfunction', 'matrixmult': 'MMUfunction', 'matrixmul': 'MMUfunction', 'mmultiplication': 'MMUfunction', 'mmultiply': 'MMUfunction', 'mmult': 'MMUfunction', 'mmul': 'MMUfunction', 'min': 'MINfunction', 'inversematrix': 'MINfunction', 'inversemat': 'MINfunction', 'inversem': 'MINfunction', 'invmatrix': 'MINfunction', 'invmat': 'MINfunction', 'invm': 'MINfunction', 'imatrix': 'MINfunction', 'imat': 'MINfunction', 'im': 'MINfunction', 'sol': 'SOLfunction', 'solve': 'SOLfunction', 'system': 'SOLfunction', 'solvesystem': 'SOLfunction', 'solveequations': 'SOLfunction', 'solvesystemofequations': 'SOLfunction', 'solsystem': 'SOLfunction', 'solequations': 'SOLfunction', 'solequation': 'SOLfunction', 'solveequation': 'SOLfunction', 'systemofequations': 'SOLfunction', 'slf': 'SLFfunction', 'solvefor': 'SLFfunction', 'solveforvariable': 'SLFfunction', 'solveforvar': 'SLFfunction', 'solfor': 'SLFfunction', 'solforvariable': 'SLFfunction', 'solforvar': 'SLFfunction', 'dom': 'DOMfunction', 'domain': 'DOMfunction', 'domainoffunction': 'DOMfunction', 'domainoffunc': 'DOMfunction', 'domainoff': 'DOMfunction', 'functiondomain': 'DOMfunction', 'funcdomain': 'DOMfunction', 'fdomain': 'DOMfunction', 'ran': 'RANfunction', 'range': 'RANfunction', 'rangeoffuction': 'RANfunction', 'rangeoffunc': 'RANfunction', 'rangeoff': 'RANfunction', 'functionrange': 'RANfunction', 'funcrange': 'RANfunction', 'functionran': 'RANfunction', 'funcran': 'RANfunction', 'frange': 'RANfunction' }

functions = [
	{
		'functionName': 'DERfunction',
		'parameterNames': ['q', 'withRespect', 'nth']
	},
	{
		'functionName': 'INTfunction',
		'parameterNames': ['q', 'withRespect']
	},
	{
		'functionName': 'INDfunction',
		'parameterNames': ['q', 'withRespect', 'min', 'max']
	},
	{
		'functionName': 'LIMfunction',
		'parameterNames': ['q', 'withRespect', 'approaches']
	},
	{
		'functionName': 'SUMfunction',
		'parameterNames': ['q', 'min', 'max']
	},
	{
		'functionName': 'MMUfunction',
		'parameterNames': ['q', 'matrix']
	},
	{
		'functionName': 'MINfunction',
		'parameterNames': ['q']
	},
	{
		'functionName': 'SOLfunction',
		'parameterNames': ['q']
	},
	{
		'functionName': 'SLFfunction',
		'parameterNames': ['q', 'withRespect']
	},
	{
		'functionName': 'DOMfunction',
		'parameterNames': ['q', 'domainOf']
	},
	{
		'functionName': 'RANfunction',
		'parameterNames': ['q', 'variableOf', 'rangeOf']
	},
	{
		'functionName': 'ToExpressionfunction',
		'parameterNames': ['q']
	}
]

@app.route("/", methods=['GET', 'POST'])
def main(): 
	from_number = request.values.get('From', None)
	body = request.values.get('Body', None)
	resp = twilio.twiml.Response()
	resp.message("Answer: " + retrieveTokens(str(body)))
	return str(resp)

if __name__ == "__main__":
    app.run(debug=True)

def retrieveTokens(body):
	originalBody = body
	funcIndices = [i for i, x in enumerate(body) if x == ':']
	if funcIndices: #puts all function calls into an array called funcCalls
		for i in funcIndices:
			endIndexOfFunctionName = i
			i -= 1
			while body[i].isalpha(): i -= 1
			parenTally = 0
			for j, item in enumerate(body[endIndexOfFunctionName + 1:]):
				if item == '(': parenTally += 1
				if item == ')': parenTally -= 1
				if parenTally == 0:
					break
			endIndexOfFunctionCall = endIndexOfFunctionName + 1 + j
			startIndexOfFunctionName = i + 1
			funcCall = body[startIndexOfFunctionName:endIndexOfFunctionName]

			# parse parameters
			if functionAliases[funcCall.lower()] == 'MMUfunction': #commas within multiple parameters
				curlyBracketTally = 0
				for i, item in enumerate(body[endIndexOfFunctionName + 2:endIndexOfFunctionCall]):
					if item == '{': curlyBracketTally += 1
					if item == '}': curlyBracketTally -= 1
					if curlyBracketTally == 0:
						break
				i += endIndexOfFunctionName + 2
				parameters = parseParameters([body[endIndexOfFunctionName + 2:i + 1], body[i + 2:endIndexOfFunctionCall]])
				output = executeMethod(functionAliases[funcCall.lower()], parameters)
				originalBody = originalBody.replace(body[startIndexOfFunctionName:endIndexOfFunctionCall + 1], output)
			elif functionAliases[funcCall.lower()] == 'MINfunction': #commans within single parameter
				parameters = parseParameters([(body[:-1].lower())[endIndexOfFunctionName + 2:endIndexOfFunctionCall]])
				output = executeMethod(functionAliases[funcCall.lower()], parameters)
				originalBody = originalBody.replace(body[startIndexOfFunctionName:endIndexOfFunctionCall + 1], output)
			elif functionAliases[funcCall.lower()] == 'INMfunction': #the special case for multivariable integrals
				parameters = parseParameters([body.replace(funcCall + ':(', 'Integrate[')[:-1] + ']'])
				output = executeMethod('ToExpressionfunction', parameters)
				originalBody = originalBody.replace(body[startIndexOfFunctionName:endIndexOfFunctionCall + 1], output)
			else: #there are no commas within any parameter(s)
				parameters = parseParameters((body[:-1].lower())[endIndexOfFunctionName + 2:endIndexOfFunctionCall].split(','))
				output = executeMethod(functionAliases[funcCall.lower()], parameters)
				originalBody = originalBody.replace(body[startIndexOfFunctionName:endIndexOfFunctionCall + 1], output)

	#every output is concatenated together and ToExpression is called on that
	parameters = parseParameters([originalBody.lower()])
	return executeMethod('ToExpressionfunction', parameters)

def parseParameters(parameters):
	for i, item in enumerate(parameters):
		parameters[i] = re.sub(r'\b(pi)\b', r'Pi', parameters[i], flags=re.I)
		parameters[i] = re.sub(r'\b(inf\b|infinity)', r'Infinity', parameters[i], flags=re.I)
	return parameters

def executeMethod(function, parameters):
	baseURL = 'https://www.wolframcloud.com/objects/user-9769a90f-f4d1-49ef-99ac-69e8a33a52eb/'
	i = 0
	while function != functions[i]['functionName']: i += 1
	URLsuffix = functions[i]['functionName'] + '?q=' + urllib.quote_plus(parameters[0])

	for pname, pvalue in zip(functions[i]['parameterNames'][1:], parameters[1:]):
		URLsuffix += '&' + urllib.quote_plus(pname) + '=' + urllib.quote_plus(pvalue)
	answer = urllib2.urlopen(baseURL + URLsuffix)
	for line in answer:
		return line
