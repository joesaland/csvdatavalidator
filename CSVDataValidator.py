# CSVDataValidator
# Version 1.0
#
# Python script which validates information in source CSV for DLP Fingerprints
#
# Eliminates bad fields based upon:
#   Known bad fields (e.g. bad or empty names)
#   Fields which fail certain regex validation checks
#   Fields outside of a particular length range
#
# Usage:
#   Arg1 - Input File data type (e.g. novalidate, employee, customer)
#   Arg2 - Input Filename
#   Arg3 - Good Output Filename
#   Arg4 - Bad Output Filename
##############################################################################

# import necessary python modules
import csv
import re
import sys

DEBUG = 0

class CSVDataValidator():
        "Provides validation dictionary and functions for validating rows"
        
        validatorList = []
        
        def __init__(self,validatorDict):
                """ Called when class is instantiated"""

                if len(validatorDict) > 0:
                
                        # get direct references to objects in validatorDict
                        self.validatorDict = validatorDict
                        self.name = validatorDict["name"]
                        self.validators = validatorDict["validators"]
                        self.numFields = len(self.validators)
                        self.maxEmptyFields = self.numFields - 1
                        self.badFieldCounters = {}
                        self.fieldNames = {}
                        
                        # precompile any regexs in the validatorList
                        for fieldNum, validator in list(self.validators.items()):
                                self.badFieldCounters[fieldNum] = 0
                                if validator["type"] == 're':
                                        validator["compiledRegex"]=re.compile(validator["regex"])
                        if DEBUG: print("Setting up validator",self.name,"number of columns",self.numFields)
                        
                        
                else:
                        # something passed an emtpy validator dictionary
                        sys.exit("CSVDataValidator class instantiated with empty validatorList")
                        

        def getHeaderNames(self, row):
        
                if len(row) > 0:
                        for index in range(len(row)):
                                self.fieldNames[index] = row[index]
                                
                                
        def validateString(self, fieldValidator, field):
                """ Validates the string in field against list of strings in stringlist""" 
                
                # check to see if empty fields are allowed
                if  len(field) == 0:
                        if fieldValidator["allowEmptyFields"] == False:
                                return False
                        else: 
                                return True
                                
                # check to see if string field matches any configured bad strings
                if field in fieldValidator["strings"]:
                        return False
                return True
        
        def validateRegex(self, fieldValidator, field):
                """ Validates string in field against regular expression in regexPattern"""
                
                # check to see if emtpy fields are allowed
                if  len(field) == 0:
                        if fieldValidator["allowEmptyFields"] == False:
                                return False
                        else: 
                                return True
                
                # check to see if field passed compiled regex
                if fieldValidator["compiledRegex"].match(field) == None:
                        return False
                return True
        
        def validateABAChecksum(self,fieldValidator, field):
                """ Validates an ABA number using checksum"""

                # grab field length once since we use it many times
                fieldLength = len(field)        

                # check to see if emtpy fields are allowed
                if  fieldLength == 0:
                        if fieldValidator["allowEmptyFields"] == False:
                                return False
                        else: 
                                return True
                
                # Validate ABA Routing Number
                if fieldValidator["validate"]:
                
                        # check to see if length is appropriate for ABA Routing Number
                        if fieldLength != 9:
                                return False
                        
                        # compute checksum,  result should be 0
                        d = [int(digit) for digit in field]
                        result = ((3*(d[0]+d[3]+d[6])) + (7*(d[1]+d[4]+d[7])) + (d[2]+d[5]+d[8])) % 10
                
                        # fail if checksum is non-zero
                        if result != 0:
                                return False
                
                return True
                
        def validateLength(self, fieldValidator, field):
                """ Validates field is a number with number of digits specified in lengthRange"""
                
                # grab field length once since we use it many times
                fieldLength = len(field)
                
                # check to see if emtpy fields are allowed
                if  fieldLength == 0:
                        if fieldValidator["allowEmptyFields"] == False:
                                return False
                        else: 
                                return True
                        
                # check to see if field is numeric
                if fieldValidator["checkNumeric"] and (fieldLength > 0) and (field.isdigit() != True): 
                        return False
                
                # grab a reference to our range 
                range = fieldValidator["range"]
                
                # Check to see if we have and meet a minimum
                if range[0] != 0:
                        if fieldLength < range[0]:
                                return False
                                
                # check to see if we have and meet a maximum
                if range[1] != -1:
                        if fieldLength > range[1]:
                                return False
                                
                return True
                
        def validateField(self, fieldIndex, field):
                """ uses validator list to validate a field"""
                
                if fieldIndex in list(self.validators.keys()):
                        # Grab a reference to the validator for this field
                        fieldValidator = self.validators[fieldIndex]
                else:
                        # Don't validate this field
                        return True
                        
                # Run the appropriate validation routine
                if fieldValidator["type"] == 'str':
                        return self.validateString(fieldValidator,field)
                elif fieldValidator["type"] == 're':
                        return self.validateRegex(fieldValidator,field)
                elif fieldValidator["type"] == 'len':
                        return self.validateLength(fieldValidator,field)
                elif fieldValidator["type"] == 'aba':
                        return self.validateABAChecksum(fieldValidator,field)
                else: 
                        sys.exit("ERROR!! BAD Validator Type"+fieldValidator["type"])
                        
                # we shouldn't get to this line but just in case
                return False
                        
        def validateRow(self,row):
                """ Validates row data
        
                Returns integer values
                        good row with all fields passing = -1
                        bad row due to number of fields = -2
                        bad row with any field failing = number of first field that failed
                """

                # Validate the row has the right number of fields
                if self.name == "novalidate":
                        if DEBUG: print("No validate selected so ignoring checks")
                        return -1

                if len(row) != len(self.validators):
                        if DEBUG: print("The number of fields in this row don't match")
                        return -2  # -2 is the error 
                
                numEmptyFields = 0

                # For each field in our row validate the field
                if DEBUG: print("Checking fields", end=' ')
                for index in range(len(row)):
                        if DEBUG: print(index, end=' ')
                        # strip extra padding in field
                        field = str(row[index].strip())
                        
                        # for each field run it's validation check)
                        if self.validateField(index, field) != True:
                                self.badFieldCounters[index] = self.badFieldCounters[index] + 1
                                if DEBUG: print()
                                return index
                
                        if len(field) == 0:
                                numEmptyFields += 1
                                if numEmptyFields >= self.maxEmptyFields:
                                        if DEBUG: print()
                                        return -3
                
                # the row passed all validations
                return -1

def loadInputCSV(CSVFileName):
        """ Loads CSV file for input data. Returns csv.reader object"""
        excelDialect = csv.excel
        excelDialect.escapechar="\\"
        inputCSVReader = csv.reader(open(CSVFileName,'r'), dialect=excelDialect, delimiter='|', quoting=csv.QUOTE_NONE)
        return inputCSVReader

def openOutputCSV(CSVFileName):
        """ Opens CSV file for writing. Returns csv.writer object"""
        excelDialect = csv.excel
        excelDialect.escapechar="\\"
        outputCSVWriter = csv.writer(open(CSVFileName,'w'), dialect=excelDialect, delimiter='|', quoting=csv.QUOTE_NONE)
        return outputCSVWriter


# This is our main program loop
if __name__ == "__main__":

        ########################################################################
        # Validator Configuration:
        #
        # Below are mixed dicts which describe the information needed
        # to configure instances of the CSVDataValidator class
        #
        # This sample shows our three possible validators
        # The first value in the dict specifies the input source data type
        # It becomes the first parameter passed as the first
        # argument of the script (e.g. employee)
        #        
        # NOTE: The last row does not have a trailing comma
        #
        # The format of a validator is:
        #       fieldnum:{"type":"validatorType", "allowEmptyFields":True|False, type specific parameters}
        #
        # The types of validators possible are:
        #       str     This is a tuple of exact matching strings
        #                       Matching a string causes a failure
        #                       Required Parameter: "strings":('badstring1","badstring2")
        #
        #       re      This is a regex pattern.
        #                       Failing the regex causes a failure
        #                       Required Parameter: "regex":r'^some regularexpression$'
        #                       The example regex in the sample below is for SSNs
        #
        #       len     This is a numeric based validation. 
        #                       Non-numeric values fails
        #                       Numeric valuse outside the length range fails
        #                       Required Parameters: "checkNumeric":True|False, "range":(#,#) where
        #                               The first number is a minimum (0 is no minimum)
        #                               The second number is a maximum (-1 is infinite length)
        #
        #       aba     This is ABA routing number validator
        #                       When the required parameter "validate" is set to True this 
        #                       validator performs a length and CRC check against the routing number
        #                       Required Parameter: "validate":True|False
        #
        #
        #       sampleValidatorDict = {
        #               "name":"samplesourcetype",
        #               "validators" : {
        #                       0:{"type":'str', "allowEmtpyFields": False, "strings":("badname1","badname2")},
        #                       1:{"type":'re',  "allowEmptyFields": False, 
        #                               "regex": (r'^(?!000)(?!666)(?!9)\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}$')},
        #                       2:{"type":"aba", "allowEmptyFields": True, "validate": True},
        #                       3:{"type":"len", "allowEmptyFields": True, "range": (4,-1)}
        #               }
        #       }
        #       sampleValidator = CSVDataValidator(sampleValidatorDict)
        #       validators[sampleValidator.name] = sampleValidator 
        ###############################################################################
        
        # Initialize our empty dictionary of configured validators
        validators = {} 
        
        ########################################################################
        # Configure all validators in the following section
        ########################################################################
        
        ########################################################################
        # novalidate validator
        # This is a special case validator which performs no checking at all
        # all data should end up in the "good" data file without change
        ########################################################################
        noValidateValidatorDict = { "name":"novalidate", "validators" : {} }
        noValidateValidator = CSVDataValidator(noValidateValidatorDict)
        validators[noValidateValidator.name] = noValidateValidator 
        # end novalidate validator
        ########################################################################
        

        ########################################################################
        # employee validator
        EmployeeValidatorDict = {
                "name":"employee",
                "validators": {
                        0:{"type":"str", "allowEmptyFields": False, "strings":()},
                        1:{"type":"re",  "allowEmptyFields": False, "regex": r'^(?!000)(?!666)(?!9)\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}$'},  #SSN regex
                        2:{"type":"aba", "allowEmptyFields": True, "validate": True},
                        3:{"type":"len", "allowEmptyFields": True, "checkNumeric":True, "range": (4,-1)}
                }
        }
        EmployeeValidator = CSVDataValidator(EmployeeValidatorDict)
        validators[EmployeeValidator.name] = EmployeeValidator 
        # end employee validator
        ########################################################################
        
        ########################################################################
        # customer validator
        CustomerValidatorDict = {
                "name":"customer",
                "validators": {
                        0:{"type":"str", "allowEmptyFields": False, "strings":()},
                        1:{"type":"re",  "allowEmptyFields": False, "regex": r'^(?!000)(?!666)(?!9)\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}$'},  #SSN regex
                        2:{"type":"aba", "allowEmptyFields": True, "validate": False},
                        3:{"type":"len", "allowEmptyFields": True, "checkNumeric":False, "range": (4,-1)}
                }
        }
        CustomerValidator = CSVDataValidator(CustomerValidatorDict)
        validators[CustomerValidator.name] = CustomerValidator
        # end customer validator
        ########################################################################

        ########################################################################
        # All validators should have been configured above this line
        # Do not modify any code after this line
        ########################################################################
        
        # build up list of configured validator names for use in error messages
        validatorNames = ""
        for validator in list(validators.values()):
                validatorNames += validator.name + " "
                
        # Check to see if we were called with the correct number of arguments
        if (len(sys.argv) != 5):
                sys.exit("Usage:\n"+
                        "  CSVDataValidator.py sourcetype inputfile goodoutputfile badoutputfile\n\n"
                        "Available sourcetype validators:\n  "+validatorNames+"\n"
                )

        # Check to see if specified validator is configured
        if (sys.argv[1]) not in list(validators.keys()):
                sys.exit("Unknown source data type: "+sys.argv[1]+"\nValid types are: "+validatorNames+"\n")
                
        # open input and output CSV files
        inputFileReader = loadInputCSV(sys.argv[2])
        goodDataFileWriter = openOutputCSV(sys.argv[3])
        badDataFileWriter = openOutputCSV(sys.argv[4])

        # choose our validator
        currentValidator = validators[sys.argv[1]]
        if DEBUG: print("We have chosen", currentValidator.name, "as our validator")

        # pull header row and put into both output files
        headerRow = next(inputFileReader)
        
        # check number of columns in header against number of fields in validator config
        if currentValidator.name != "novalidate" and len(headerRow) != len(currentValidator.validators):
                sys.exit("Number of fields in input does not match "+currentValidator.name+" config. Got:" +
                str(len(headerRow)) + " Expected:" + str(len(currentValidator.validators)))
        
        currentValidator.getHeaderNames(headerRow)
        
        # write out header rows to our output files
        goodDataFileWriter.writerow(headerRow)
        
        badHeaderRow = list(headerRow)
        badHeaderRow.append("ERROR_MESSAGE")
        badDataFileWriter.writerow(badHeaderRow)
                        
        # intialize counters
        goodRowCounter = 0
        badRowCounter = 0
        totalRowCounter = 0
        
        # Validate, count, and write out rows
        for row in inputFileReader:
                #print row
                totalRowCounter += 1
                result = currentValidator.validateRow(row)
                if DEBUG: print("Row",totalRowCounter,"result",result)
                if result == -1:
                        goodRowCounter += 1
                        goodDataFileWriter.writerow(row)
                elif result == -2:
                        badRowCounter +=1
                        row.append("INCORRECT NUMBER OF FIELDS")
                        badDataFileWriter.writerow(row)
                elif result == -3:
                        badRowCounter +=1
                        row.append("TOO MANY EMPTY FIELDS")
                        badDataFileWriter.writerow(row)
                else:
                        badRowCounter += 1
                        if len(row[result]) > 0:
                                row.append("BAD DATA IN FIELD: "+currentValidator.fieldNames[result]+" VALUE: "+row[result])
                        else:
                                row.append("BAD DATA IN FIELD: "+currentValidator.fieldNames[result]+" VALUE: EMPTY")
                        badDataFileWriter.writerow(row)
        
        # Print out final counts
        print("")
        print("Results:")
        print("-----------------------------------------------------------------")
        print("Total number of rows (excluding header): ", totalRowCounter)
        print("Number of good rows: ", goodRowCounter)
        print("Number of bad rows: ", badRowCounter)
        print("")
        for fieldNum,count in list(currentValidator.badFieldCounters.items()):
                print("Field:",currentValidator.fieldNames[fieldNum],"\t\t Count:",count)
