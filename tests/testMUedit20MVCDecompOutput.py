import unittest
import filecmp
import os

# init file paths by combining cwd and file name
OUTPUTED20MVCFILE = "trial1_20MVC.otb+_decomp.mat"
EXPECTED20MVCFILE = "ExpectedOutput_trial1_20MVC.otb+_decomp.mat"


expectedOutput = os.path.join(os.getcwd(), EXPECTED20MVCFILE)
actualOutput = os.path.join(os.getcwd(), "..", "data", "io", "input_decomposition", OUTPUTED20MVCFILE)

# debug 
print(expectedOutput)
print(actualOutput)

print("test 1: MUedit output from trial1 20MVC = provided output")
isSame = filecmp.cmp(expectedOutput, actualOutput, shallow= False)
print(isSame)