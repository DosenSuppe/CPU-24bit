import sys

#
#   To-Do:
#       - linking multiple asm-files together, creating one program "!link ./file.asm"
#       - importing dosm-image files on demand: "!import ./image.dosm"
#         the image is translated into the x, y cordinations (1 = pixel; 0 = no pixel)
#   
#       - interpreter for dosb-files using asm "!run ./file.dosb"
#       
#   new keywords:
#       !link       ./file.asm
#       !import     ./image.dosm    OR !import  ./text.txt
#       !run        ./file.dosb
#

INSTR_SET_ONE = {
    "nop":"0000",
    "halt":"0001",
    "lda":["0002", "0003"],
    "sta":"0004",
    "ldb":["05", "06"],
    "stb":"07",

    "add":["08", "09"],
    "sub":["0a", "0b"],
    "mul":["0c", "0d"],
    "div":["0e", "0f"],
    
    "jp":"10",
    "jpz":"11",
    "outa":"12",
    "outb":"13",
    "out":["14", "15"],

    "mod":["16", "17"]
}

CHARACTER_SET = {
    "\n":"000a", # 0001010
    
    "0":"0030", # 0110000
    "1":"0031", # 0110001
    "2":"0032", # 0110010
    "3":"0033", # 0110011
    "4":"0034", # 0110100
    "5":"0035", # 0110101
    "6":"0036", # 0110110
    "7":"0037", # 0110111
    "8":"0038", # 0111000
    "9":"0039", # 0111001

    "a":"0061", "A":"0041", # 1100001, 1000001 
    "b":"0062", "B":"0042", # 1100010, 1000010  
    "c":"0063", "C":"0043", # 1100011, 1000011  
    "d":"0064", "D":"0044", # 1100100, 1000100  
    "e":"0065", "E":"0045", # 1100101, 1000101  
    "f":"0066", "F":"0046", # 1100110, 1000110  
    "g":"0067", "G":"0047", # 1100111, 1000111  
    "h":"0068", "H":"0048", # 1101000, 1001000  
    "i":"0069", "I":"0049", # 1101001, 1001001  
    "j":"006a", "J":"004a", # 1101010, 1001010  
    "k":"006b", "K":"004b", # 1101011, 1001011  
    "l":"006c", "L":"004c", # 1101100, 1001100  
    "m":"006d", "M":"004d", # 1101101, 1001101  
    "n":"006e", "N":"004e", # 1101110, 1001110  
    "o":"006f", "O":"004f", # 1101111, 1001111  
    "p":"0070", "P":"0050", # 1110000, 1010000  
    "q":"0071", "Q":"0051", # 1110001, 1010001  
    "r":"0072", "R":"0052", # 1110010, 1010010  
    "s":"0073", "S":"0053", # 1110011, 1010011  
    "t":"0074", "T":"0054", # 1110100, 1010100  
    "u":"0075", "U":"0055", # 1110101, 1010101  
    "v":"0076", "V":"0056", # 1110110, 1010110  
    "w":"0077", "W":"0057", # 1110111, 1010111  
    "x":"0078", "X":"0058", # 1111000, 1011000  
    "y":"0079", "Y":"0059", # 1111001, 1011001  
    "z":"007a", "Z":"005a", # 1111010, 1011010  
 
    ".":"002e", # 0101110
    ",":"002c", # 0101100
    "!":"0021", # 0100001
    "?":"007f", # 0111111
    "*":"002a", # 0101010
    "+":"002b", # 0101011
    "-":"002d", # 0101101
    "/":"002f", # 0101111
    "\\":"005c",# 1011100
    "(":"0028", # 0101000
    ")":"0029", # 0101001
    "{":"007b", # 1111011
    "}":"007d", # 1111101
    "[":"005b", # 1011011
    "]":"005d", # 1011101
    "_":"005f", # 1011111
    "$":"0024", # 0100100
    "#":"0023", # 0100011
    "%":"0025", # 0100101
    "&":"0026", # 0100110
    "@":"0040", # 1000000
    "^":"005e", # 1011110
    "~":"007e", # 1111110
    "<":"0070", # 0111100
    ">":"003e", # 0111110
    "=":"003d", # 0111101
    ";":"003b", # 0111011
    ":":"003a", # 0111010
    "\"":"0022",# 0100010
    " ":"0020", # 0100000
}

INSTR_SET_TWO = {
    "nop":"0000",         # no-op
    "halt":"0001",        # halt program
    "lda":["0002", "0003"], # load into A-Register
    "sta":"0004",         # store A-Register
    # "ldb":["0005", "0006"], # load into B-Register
    # "stb":"0007",         # store B-Register
    "add":["0005", "0006"], # add to A-Register
    "sub":["0007", "0008"], # sub from A-Register
    "out":["0009", "000a"], # display value
    "jp":"000b",          # jump to label
    "jpz":"000c",         # jump to label on zero
    "jpc":"000d",         # jump to label on carry
    "rts":"000e",         # return to subroutine
    "lb":"000f",          # loop-back to label (does not change RTS)
    "lbz":"0010",         # loop-back to label on zero
    "lbc":"0011",         # loop-back to label on carry
    "rtc":"0012",         # return to subroutine on carry
    "rtz":"0013",         # return to subroutine on zero
    "lpc":["0014", "0015"], # load value into Program-Counter
    "spc":"0016",         # store value of Program-Counter
    
    "dc":"0017",          # clears the contents of the graphic display
    "tc":"0018",          # clears the contents of the terminal
    
    "tw":"0019",          # writes character to terminal
    "dw":["001a", "001b"],# sets pixel to value

    "co":"001c",
    "ct":"001d"

}

INSTRUCTIONS = INSTR_SET_TWO

JUMP_POINTS = {}
JUMP_POINTS_AWAIT = {}

def tokenizer(inputString):
    tokens = []
    isComment = False

    curPos = 0
    curLine = 0
    nexLine = 1

    curWord = ""

    while (curPos < len(inputString)):
        curChar = inputString[curPos]

        if (curChar == " " or curChar == "\n" or curChar == "\t"):
            if (len(curWord)>0 and curWord!=" "):
                if (not isComment):
                    val = INSTRUCTIONS.get(curWord.lower()) or curWord
                    tokens.insert(len(tokens)+1, val)
            
            if (curChar == "\n"):
                isComment = False
                
            curWord = ""

        elif (curChar == ";"): # removing comments
                isComment = True
                
        else:
            curWord = curWord+curChar

        curPos += 1

    return tokens

def getTextFrom(token):
    result=""
    token = token[1: len(token)-1]
    curPos = 0
    
    while (curPos < len(token)):
        
        curChar = token[curPos]
        nexChar = None
        if (curPos+1 < len(token)):
            nexChar = token[curPos+1]

        if (curChar == "\\" and nexChar != None):
            if (curChar+nexChar == "\s"):
                result = result + CHARACTER_SET[" "] + " "
                curPos += 1
            elif (curChar+nexChar == "\\n"):
                result = result + CHARACTER_SET["\n"] + " "
                curPos += 1
        else:
            result = result + CHARACTER_SET[curChar] + " "

        curPos += 1

    return result

def grammar2(tokens):
    RESULT = []

    save = False

    curPos = 0
    resPos = 0
    resTok = ""

    while (curPos < len(tokens)):
        curTok = tokens[curPos]
        nextTok = None

        if (curPos+1 < len(tokens)):
            nextTok = tokens[curPos+1]

        if (type(curTok)==list):
            if (nextTok != None):
                if (nextTok[0]=="["):
                    resTok = curTok[1]
                    tokens[curPos+1] = nextTok[1:len(nextTok)-1]

                else:
                    resTok = curTok[0]

                # keep the lines below out of shame, this line 
                # below has cost me 2h of debugging to find as 
                # issue for skipping bytes!!

                # curPos += 1

        else: # adding the token to the result
            # removing formatting to retreive value

            if (curTok[0:2] == "0x"):
                curTok = curTok[2:len(curTok)]

            # handling new labels
            if (curTok[0] == ":"):
                JUMP_POINTS[curTok[1:len(curTok)]] = format(resPos, '02x')

                for key in JUMP_POINTS_AWAIT.keys():
                    positions = JUMP_POINTS_AWAIT[key]
                    pointer = JUMP_POINTS.get(key)  # label name
                    
                    if (pointer):
                        # checking for multiple calls for same label
                       
                        if (type(positions) == list):
                            for position in positions:
                                RESULT[position-1] = pointer
                
                curPos += 1
                curTok = ""
                continue

            elif (curTok[0] == "#"):
                curTok = hex(int(curTok[1:len(curTok)]))
                curTok = curTok[2:len(curTok)]

            elif (curTok[0] == "$" and curTok[len(curTok)-1] == "$"): # $Hello World!$=f000
                text = getTextFrom(curTok)
                curTok = text
            
            foundJump = JUMP_POINTS.get(curTok)

            if (foundJump):
                curTok = foundJump
            else:
                save = True

            

            resTok = curTok

        if (len(resTok)>0):
            RESULT.insert(len(RESULT), resTok)
            resPos += 1

            if (save):
                if (len(resTok)>2):
                    _list = JUMP_POINTS_AWAIT.get(resTok)
                    if (_list):
                        _list.insert(len(_list), resPos)
                    else:
                        JUMP_POINTS_AWAIT[resTok] = [resPos]
                    
                save = False

            resTok = ""
        
        curPos += 1

    # print(RESULT)
    return RESULT


def loadFile(file_name):
    file = open(file_name, "r")
    res = file.read()
    file.close()
    return res

arguments_num = len(sys.argv)
PRINT_RESULT = False
file_name = None

if (arguments_num == 4):
    file_name = sys.argv[2]
    PRINT_RESULT = True

elif (arguments_num == 3):
    file_name = sys.argv[1]

else:
    print("!! NO FILE PROVIDED !!")
    exit(0)
    
CONTENT = loadFile(file_name)
TOKENS = tokenizer(CONTENT)
GRAMMAR = grammar2(TOKENS)

if (PRINT_RESULT):
    print(" ")
    print("DECODED TOKENS:")
    print(TOKENS)
    print("------------------------------------")
    print("\nAST-Applied: ")
    print(GRAMMAR)
    print("------------------------------------")
    res = ""

    count = 0
    for item in GRAMMAR:
        count += 1
        res+=str(item)+" "
    print("\nRaw-Binary: ")
    print(res)
    print(" ")
    print("Bytes:\n" + str(len(GRAMMAR)) + " / " + str(2**16) + "\n" + str(len(GRAMMAR)/2**16) + "% Used")
    print(" ")
    
    print("#Include <sub-routine>")
    for i in JUMP_POINTS:
        print("\t:"+i)

FORMAT_GRAMMAR = ""
if (INSTRUCTIONS == INSTR_SET_TWO):
    FORMAT_GRAMMAR = "v2.0 raw\n"
FORMAT_WIDTH = 10
COUNTER = 1

for element in GRAMMAR:
    if (COUNTER%FORMAT_WIDTH == 0):
        FORMAT_GRAMMAR = FORMAT_GRAMMAR + GRAMMAR[COUNTER-1] + "\n"
    else:
        FORMAT_GRAMMAR = FORMAT_GRAMMAR + GRAMMAR[COUNTER-1] + " "

    COUNTER += 1


outputFilename = ""
if (len(sys.argv) == 4):
    outputFilename = sys.argv[3]
else:
    outputFilename = sys.argv[2]

outputFile = open(outputFilename+".o", "w")
outputFile.write(FORMAT_GRAMMAR)
outputFile.close()
