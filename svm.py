# used for csv data manipulation
import pandas as pd 

# used in obtaining arguments
import sys

# used for svm and the metrics 
from sklearn import svm, metrics

# used for getting project constants
import constants as c

# accepts arguments
# sys.argv[1] = filepath to the output.csv
# sys.argv[2] = percentage for training (optional)

if len(sys.argv) > 1:
    csv_file = sys.argv[1]
    try:
        try:
            TRAIN_PERCENT_IN_DECIMAL = float(sys.argv[2])
        except Exception as iden:
            TRAIN_PERCENT_IN_DECIMAL = c.TRAIN_PERCENT 
        data = pd.read_csv(csv_file)
    except Exception as e:
        print("Please input the correct .CSV file.")
        exit()
else:
    print("Please include the path to the csv file (output.csv) in the arguments")
    exit()

# informative print statements
print(str(TRAIN_PERCENT_IN_DECIMAL * 100) + "%" + " used for training" )
print(str(data.shape[0]) + " rows obtained.")
class_stats = data.groupby('aggressive').size()
print("Aggressive : " + str(class_stats[0]))
print("Non-aggressive : " + str(class_stats[1]))
print("Total : " + str(class_stats[0] + class_stats[1]))

# number of rows to obtain for training
train = int(TRAIN_PERCENT_IN_DECIMAL * data.shape[0])


# shuffling the data
print("dataset shuffled")
data = data.sample(frac=1).reset_index(drop=True)

# making subsets for training set
for_training = data[:train]                                     # first 'train' number of rows
features = for_training.drop(['name','aggressive'], axis=1)     # dropping name and class
classes = for_training[['aggressive']]                          # getting only class

# display how much is aggressive, not aggressive
print("------------------------------------")
print("Training Dataset")
agg = for_training.groupby('aggressive').size()
print("Aggressive : " + str(agg[0]))
print("Non-aggressive : " + str(agg[1]))
print("Total : " + str(agg[0] + agg[1]))
print("------------------------------------")

# making subsets for testing set
for_testing = data[train:]                                      # rows after index 'train'
test_features = for_testing.drop(['name','aggressive'], axis=1) # drop name and class
test_classes = for_testing[['aggressive']]                      # get only class

# display how much is aggressive, not aggressive
print("------------------------------------")
print("Testing Dataset")
test_agg = for_testing.groupby('aggressive').size()             # groupby to aggregate the number of aggressive/non-aggressive tuples
print("aggressive : " + str(test_agg[0]))
print("non-aggressive : " + str(test_agg[1]))
print("Total : " + str(test_agg[0] + test_agg[1]))
print("------------------------------------")

# feeds/trains the model
svc = svm.SVC(kernel='rbf', C=1,gamma='auto').fit(features, classes.values.ravel())

# lets the svm predict classes/values
pred = svc.predict(test_features)

print("Precision: " + str(metrics.precision_score(test_classes,pred)))

print("Recall: " + str(metrics.recall_score(test_classes,pred)))

print("Confusion Matrix:\n" + str(metrics.confusion_matrix(test_classes,pred)))

print("Accuracy: " + str(metrics.accuracy_score(test_classes,pred)))