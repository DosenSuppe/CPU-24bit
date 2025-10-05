import sys 

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

INSTRUCTION_SET = {
    "nop":"0000",         # no-op
    "halt":"0001",        # halt program
    "lda":["0002", "0003"], # load into A-Register
    "sta":"0004",         # store A-Register
    "ldb":["0005", "0006"], # load into B-Register
    "stb":"0007",         # store B-Register
    "add":["0008", "0009"], # add to A-Register
    "sub":["000a", "000b"], # sub from A-Register
    "outa":"000c",        # display A-Register
    "outb":"000d",        # display B-Register
    "out":["000e", "000f"], # display value
    "jp":"0010",          # jump to label
    "jpz":"0011",         # jump to label on zero
    "jpc":"0012",         # jump to label on carry
    "rts":"0013",         # return to subroutine
    "lb":"0014",          # loop-back to label (does not change RTS)
    "lbz":"0015",         # loop-back to label on zero
    "lbc":"0016",         # loop-back to label on carry
    "rtc":"0017",         # return to subroutine on carry
    "rtz":"0018",         # return to subroutine on zero
    "lpc":["0019", "001a"], # load value into Program-Counter
    "spc":"001b",         # store value of Program-Counter
    
    "dc":"001c",          # clears the contents of the graphic display
    "tc":"001d",          # clears the contents of the terminal
    
    "tw":"001e",          # sets pixel to value
    "dr":"001f",          # resets pixel
    "dw":"0020",          # writes character to terminal
}

MEMORY = {}
for i in range(0xffff):
    MEMORY[i] = "0000"

PARTITIONS = {
    "PROG_MEM":[0x0000, 0xa000],        # 40960 bytes
    "VARIABLE_MEM":[0xa001, 0xd000],    # 12287 bytes
    "BUFFER_MEM":[0xd001, 0xf000],      # 8191  bytes
    "SYSTEM_MEM":[0xf001, 0xfff0]       # 4079  bytes
}

#
#   Pointers
#
PROG_POINTER = 0x0000 # pointing towards the current location in Program memory
VARIABLE_POINTER = 0xa001 # pointing towards the next available place in Variable memory
BUFFER_POINTER = 0xd001 # pointing towards the next available place in Buffer memory 
SYSTEM_POINTER = 0xf001 # pointing towards the current location in System memory

#
#   JUMP-LABELS
#

JUMP_LABELS = {}
JUMP_LABELS_AWAIT = {}

#
#   TRANSLATING
#

# parsing the string into idividual tokens
def tokenizer(inputString):
    tokens = []

    curPos = 0
    curWord = ""

    while (curPos < len(inputString)):
        curChar = inputString[curPos]

        if (curChar == " " or curChar == "\n" or curChar == "\t"):
            if (len(curWord)>0 and curWord!=" "):
                val = INSTRUCTION_SET.get(curWord.lower()) or curWord
                tokens.insert(len(tokens)+1, val)
            curWord = ""

        else:
            curWord = curWord+curChar

        curPos += 1

    return tokens

# translate any string into ascii-bytes for Logisim
def getTextFrom(token, buffer_pointer):
    result= {}
    token = token[1: len(token)-1]
    curPos = 0

    while (curPos < len(token)):
        
        curChar = token[curPos]
        nexChar = None
        if (curPos+1 < len(token)):
            nexChar = token[curPos+1]

        if (curChar == "\\" and nexChar != None):
            if (curChar+nexChar == "\s"):
                result[buffer_pointer] = CHARACTER_SET[" "]
                buffer_pointer = buffer_pointer + 1

                curPos += 1
            elif (curChar+nexChar == "\\n"):
                result[buffer_pointer] = CHARACTER_SET["\n"]
                buffer_pointer = buffer_pointer + 1
                curPos += 1
        else:
            result[buffer_pointer] = CHARACTER_SET[curChar]
            buffer_pointer = buffer_pointer + 1
            
        curPos += 1

    print(result)
    return [result, buffer_pointer]

def grammar2(tokens, buffer_pointer):
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
                JUMP_LABELS[curTok[1:len(curTok)]] = format(resPos, '02x')

                for key in JUMP_LABELS_AWAIT.keys():
                    positions = JUMP_LABELS_AWAIT[key]
                    pointer = JUMP_LABELS.get(key)  # label name
                    
                    if (pointer != None):
                        if (len(pointer)<4):
                            if (len(pointer) == 1):
                                pointer = "000"+pointer
                            elif (len(pointer) == 2):
                                pointer = "00"+pointer
                            elif (len(pointer) == 3):
                                pointer = "0"+pointer

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
                if (len(curTok)<4):
                    if (len(curTok) == 1):
                        curTok = "000"+curTok
                    elif (len(curTok) == 2):
                        curTok = "00"+curTok
                    elif (len(curTok) == 3):
                        curTok = "0"+curTok

            elif (curTok[0] == "$" and curTok[len(curTok)-1] == "$"): # $Hello World!$=f000
                stringRes = getTextFrom(curTok, buffer_pointer)
                buffer_pointer = stringRes[1]
                if (stringRes[1] == "ALLOCATION FAILED"):
                    print("ALLOCATION FAILED; ISSUES MAY OCCUR WHEN PROGRAM IS RUN")

                for key in stringRes[0].keys():
                    MEMORY[key] = stringRes[0][key]
                curTok = "0000"

            foundJump = JUMP_LABELS.get(curTok)

            if (foundJump):
                curTok = foundJump
                if (len(curTok)<4):
                    if (len(curTok) == 1):
                        curTok = "000"+curTok
                    elif (len(curTok) == 2):
                        curTok = "00"+curTok
                    elif (len(curTok) == 3):
                        curTok = "0"+curTok
                        
            else:
                save = True

            
            resTok = curTok

        if (len(resTok)>0):
            if (len(resTok)<4):
                    if (len(resTok) == 1):
                        resTok = "000"+resTok
                    elif (len(resTok) == 2):
                        resTok = "00"+resTok
                    elif (len(resTok) == 3):
                        resTok = "0"+resTok
                        
            RESULT.insert(len(RESULT), resTok)
            resPos += 1

            if (save):
                if (len(resTok)>2):
                    _list = JUMP_LABELS_AWAIT.get(resTok)
                    if (_list):
                        _list.insert(len(_list), resPos)
                    else:
                        JUMP_LABELS_AWAIT[resTok] = [resPos]
                    
                save = False

            resTok = ""
        
        if (len(curTok)<4 and type(curTok) != list):
            if (len(curTok) == 1):
                curTok = "000"+curTok
            elif (len(curTok) == 2):
                curTok = "00"+curTok
            elif (len(curTok) == 3):   
                 curTok = "0"+curTok

        curPos += 1

    # print(RESULT)
    return RESULT



#
#   Input-Handling
#

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
GRAMMAR = grammar2(TOKENS, BUFFER_POINTER)

counter = 0
for _i in GRAMMAR:
    MEMORY[counter] = GRAMMAR[GRAMMAR.index(_i)]
    counter +=1 

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
    print("Bytes:\n" + str(len(GRAMMAR)) + " / 255\n")
    
    print("#Include <sub-routine>")
    for i in JUMP_LABELS:
        print("\t:"+i)

FORMAT_GRAMMAR = "v2.0 raw\n"
FORMAT_WIDTH = 10
COUNTER = 1

for element in MEMORY:
    if (COUNTER%FORMAT_WIDTH == 0):
        FORMAT_GRAMMAR = FORMAT_GRAMMAR + MEMORY[element] + "\n"
    else:
        FORMAT_GRAMMAR = FORMAT_GRAMMAR + MEMORY[element] + " "

    COUNTER += 1

# for element in GRAMMAR:
#    if (COUNTER%FORMAT_WIDTH == 0):
#        FORMAT_GRAMMAR = FORMAT_GRAMMAR + GRAMMAR[COUNTER-1] + "\n"
#    else:
#        FORMAT_GRAMMAR = FORMAT_GRAMMAR + GRAMMAR[COUNTER-1] + " "
#
#    COUNTER += 1


outputFilename = ""
if (len(sys.argv) == 4):
    outputFilename = sys.argv[3]
else:
    outputFilename = sys.argv[2]

outputFile = open(outputFilename+".o", "w")
outputFile.write(FORMAT_GRAMMAR)
outputFile.close()

