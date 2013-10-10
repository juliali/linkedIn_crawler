from __future__ import division
import collections
import math
from optparse import OptionParser

def commandLineArgs():
    parser = OptionParser()
    parser.add_option('--test-file', dest = 'test_file',help = 'input file continas data for testing, in arff formate')
    parser.add_option('--train-file', dest = 'train_file',help = 'input file continas data for training, in arff formate')
    (options, args) = parser.parse_args()
    
    if not options.train_file:   # if filename is not given
        parser.error('Training file is not given')
    return options

class Model:
        def __init__(self, arffFile):
            self.trainingFile = arffFile
            self.features = {}      #all feature names and their possible values (including the class label)
            self.featureNameList = []       #this is to maintain the order of features as in the arff
            self.featureCounts = collections.defaultdict(lambda: 1)#contains tuples of the form (label, feature_name, feature_value)
            self.featureVectors = []        #contains all the values and the label as the last entry
            self.labelCounts = collections.defaultdict(lambda: 0)   #these will be smoothed later
 
        def GetValues(self):
            file = open(self.trainingFile, 'rb')            
            for line in file:
                if line[0] != '@':  #start of actual data
                    self.featureVectors.append(line.strip().lower().split(','))
                else:   #feature definitions
                    if line.strip().lower().find('@data') == -1 and (not line.lower().startswith('@relation')):
                        self.featureNameList.append(line.strip().split()[1])
                        self.features[self.featureNameList[len(self.featureNameList) - 1]] = line[line.find('{')+1: line.find('}')].strip().split(',')

            file.close()
            return
    
        def TrainClassifier(self):
            for fv in self.featureVectors:
                self.labelCounts[fv[len(fv)-1]] += 1 #udpate count of the label
                for counter in range(0, len(fv)-1):
                    feature_items = fv[counter].split(';')
                    for fi in feature_items:
                        if fi is not None and not fi == '':
                            #print "label: ", fv[len(fv)-1]
                            #print "counter: ", counter, " len(fv) -1 == ", len(fv) -1
                            #print "featureName: ", self.featureNameList[counter]
                            #print "feature: ", fi
                            self.featureCounts[(fv[len(fv)-1], self.featureNameList[counter], fi)] += 1
 
            for label in self.labelCounts:  #increase label counts (smoothing). remember that the last feature is actually the label
                for feature in self.featureNameList[:len(self.featureNameList)-1]:
                    self.labelCounts[label] += len(self.features[feature])

            return

        def Classify(self, featureVector):      #featureVector is a simple list like the ones that we use to train
            probabilityPerLabel = {}
            for label in self.labelCounts:
                logProb = 0
                for featureValue in featureVector:
                    feature_items = featureValue.split(';')
                    for fi in feature_items:
                        logProb += math.log(self.featureCounts[(label, self.featureNameList[featureVector.index(featureValue)], fi)]/self.labelCounts[label])
                probabilityPerLabel[label] = (self.labelCounts[label]/sum(self.labelCounts.values())) * math.exp(logProb)
            print probabilityPerLabel
            return max(probabilityPerLabel, key = lambda classLabel: probabilityPerLabel[classLabel])
    
        def TestClassifier(self, arffFile):
            file = open(arffFile, 'r')
            total_num = 0
            succeed_num = 0
            
            for line in file:
                if line[0] != '@':
                    vector = line.strip().lower().split(',')
                    predict = self.Classify(vector)
                    real = vector[len(vector) - 1]
                    result = "Failed"
                    if predict == real:
                        result = "Bingo!"
                    print "[classifier result]: " + predict + "; [given]: " + real + " -- " + result
                    total_num += 1
                    if result == "Bingo!":
                        succeed_num += 1

            accuracy = succeed_num / total_num * 100
            print "Accuracy is: " + str(accuracy) + "%"
            return

        
if __name__ == "__main__":
        options = commandLineArgs()
        if options.train_file is not None:
            train_file = options.train_file
        if options.test_file is not None:
            test_file = options.test_file
        else:
            test_file = train_file
    
        model = Model(train_file)
        model.GetValues()
        model.TrainClassifier()
        model.TestClassifier(test_file)
