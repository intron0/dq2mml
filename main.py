#Author: intron
def spc():

    def fetchInt(file):
        return int(file.read(1).hex(), 16)
    def fetchHex(file):
        return file.read(1).hex()
    def intToHex(i):
        return hex(int(i))[2:]
    def fetchLE(inp):
        lsb = fetchInt(inp)
        msb = fetchInt(inp)
        return (msb * 256 + lsb)
    spc_header_size=0x100

    ##params:
    insReplace = {0: 30, 1: 31, 2: 32, 3: 33, 4: 34, 5: 33, 6: 34, 7: 35, 8: 36, 9: 34, 10: 37, 11: 38}
    # insReplace={0:31, 1:30,2:30, 3:30,4:30, 5:30,6:30, 7:30, 8:30,9:30, 10:30,11:30}
    echoSize=2
    jumpLimit = 8  # if the song loops, change this number to something like 5, increase to  if it gets cutted. manually trim the .txt tracks to loop perfectly.
    if True:
        inp=open("./dq6-29.spc","rb")
        head = 0x8e04 #paste value from vgmtrans
    else:
        inp = open("./dq3-32.spc", "rb")
        head = 0x9848
    #end params

    inp.seek(head + spc_header_size +2, 0)
    tracks=[]
    for i in range(0,8):
        off=fetchLE(inp)
        if off != 0:
            tracks.append(head+off)

    outp='''#amk 2
#spc

{
	#author "author"
	#title	"song"
	; converted via dq2mml by intron
}
#path "DQ"
#samples
{
    #default
    "strings.brr"
	"stringsLow.brr"
}
#instruments
{
 "strings.brr"        $FF $E0 $00 $03 $68    ;@30
 "stringsLow.brr"		$FF $EC $00 $0f $68    ;@31  
 @0 $FF $E0 $00 $03 $00 ;32 
 @11 $CF $E0 $00 $03 $00 ;33  
 @2 $FF $E5 $00 $01 $80 ;34 # star 
 @11 $CF $E0 $00 $03 $00;@11 19 $CF $E0 $00 $03 $00 ;35 4:40 0:20
 @4 $FF $E0 $00 $03 $00 ;36 bajo2
 @12 $FF $E0 $00 $07 $80 ;37 3:54
 @10 $FF $E0 $00 $03 $00 ;38  4:10
}

;#0 v255 w160 t110
;a8
;/
;v30
;l2[@22cccc]120

'''

    subPatternIds=set()
    
    def scan(where, outp, subPattern=False):
        inp.seek(where+spc_header_size, 0)
        actualOctave = -1
        timesJumped=0
        durationStr=""
        adsr = [7, 7, 7, 7, 7]
        if subPattern:
            chunkLeft=outp[0:outp.find(f"({where})")+len(f"({where})")]
            chunkRight=outp[outp.find(f"({where})")+len(f"({where})"):]
            outp=""
            inp.seek(head, 1)
        while True:
            b=inp.read(1)
            if b==b'':
                print("error eof")
                break
            elif b==b'\xeb':
                outp+=f"\n$F1 ${intToHex(echoSize)} " #fixed
                outp+=f"${intToHex(fetchInt(inp)*3)} "
                outp+=f"${fetchHex(inp)} ;echo 2:delay,feedback,fir\n"
                fetchHex(inp)
            elif b==b'\xea':
                outp+="\n;$EF $ff " #cmd ignored as this cmd must know echo ch state
                outp+=f"${fetchHex(inp)} "
                outp+=f"${fetchHex(inp)} ;echo vol:channels on,l,r\n"
            elif b == b'\xef':
                outp+="\n$F5 "
                for i in range(1,9):
                    outp+=f"${fetchHex(inp)} "
                outp+=f" ;fir\n"
            elif b == b'\xdb':
                outp+=f"w{int(fetchInt(inp)*0.9)} "#mvol
            elif b == b'\xe3':
                outp+=f"v{int(fetchInt(inp))} \n"#vol
            elif b == b'\xdd':
                outp+=f"\nt{int(fetchInt(inp)*(60000000/12240000)*0.4)} \n"#tempo
            elif b == b'\xee': #echo on on this ch
                outp+=f"\n$f4 $03 ;echo on\n" #warn,amk command to Toggle echo
            elif 1 <= int(b.hex(),16) <= 0x7f: #note param
                ticks=int(b.hex(),16)
                qty96s=int(int(b.hex(),16)/1)
                minmeasure=96
                durationStr=f"96"
                for abc in range(0,qty96s):
                    if abc==0:
                        durationStr = f"{minmeasure}"
                    else:
                        durationStr += f"^{minmeasure}"
                durationStr = durationStr.replace("96^96^96", "32")
                durationStr = durationStr.replace("96^96", "48")
                durationStr = durationStr.replace("48^48", "24")
                durationStr = durationStr.replace("24^24", "12")
                durationStr = durationStr.replace("12^12", "6")
                durationStr=durationStr.replace("64^64","32")
                durationStr=durationStr.replace("32^32", "16")
                durationStr=durationStr.replace("16^16", "8")
                durationStr=durationStr.replace("8^8", "4")
                durationStr=durationStr.replace("4^4", "2")
                durationStr=durationStr.replace("2^2", "1")
                #outp += f";l{durationstr}\n"
                outp += " "
                a=inp.read(1)
                if int(a.hex(),16) < 0x80:
                    outp+=f"q{a.hex()} "
                else:
                    inp.seek(-1,1)
            elif 0x80 <= int(b.hex(),16) <= 0xcf: #a note
                #if 0x80 <= int(b.hex(), 16) <= 0xc5:
                octaves=[*range(1,7)]
                notes=["c","c+","d","d+","e","f","f+","g","g+","a","a+","b"]
                octave = int((int(b.hex(), 16) - 0x80 -1) / 12)
                note = (int(b.hex(), 16) - 0x80 -1) % 12
                if actualOctave!= octave:
                    if actualOctave == octave-1:
                        outp+=f"> "
                    elif actualOctave == octave+1: #lower
                        outp+=f"< "
                    else:
                        outp+=f"o{octaves[octave]} "
                    actualOctave = octave

                outp+=f"{notes[note]}{durationStr} "
            elif b == b'\xf3': #call

                off=fetchLE(inp)
                outp+=f"  ({off}) "
                subPatternIds.add(off)
            elif b == b'\xf2':
                outp+=f"  ;jumped\n"
                timesJumped+=1
                num=fetchLE(inp)+head
                if timesJumped==jumpLimit:
                    break
                inp.seek(num+spc_header_size,0)

            elif b == b'\xf9':
                subcmd=fetchInt(inp)
                if  subcmd== 9:
                    a=fetchInt(inp)
                    b=fetchInt(inp)
                    if a not in [0,1]: a=1
                    if b not in [0,1]: b = 1
                    outp+=f"y10,{a},{b} ;surround \n" #disadvantage:resets pan for simplicity
                elif 3 <= subcmd <= 7:
                    val=fetchInt(inp)
                    if subcmd==7 :
                        #outp += f"v{val * 6 + 30} ;adsr Set Sustain Rate \n" ????
                        val=int(val/4.4)
                        subcmd=5
                    adsr[subcmd-3]=val
                    DA= (adsr[1]*16+adsr[0])%128
                    SR = adsr[2] * 32 + adsr[3]

                    next=hex(fetchInt(inp))
                    next2 = fetchInt(inp)
                    if not (next=="0xf9" and (3 <= next2 <= 7)):
                        outp += f"$ED ${DA:x} ${SR:x} ;adsr\n"
                    inp.seek(-2, 1)

                #elif subcmd==7:
                    #outp += f"v{fetchInt(inp)*6+30} ;adsr Set Sustain Rate \n"


                elif subcmd == 0:
                    loopcount=fetchInt(inp)
                    outp+=" [[ "
                elif subcmd == 1:
                    if "loopcount" in locals():
                        outp+=f" ]]{loopcount} "
                    else:
                        print("warn: ignored 'return from call' cmd outside a call")
                    inp.seek(2, 1)
                else:
                    input("error unk subcmd")


            elif b == b'\xd6':
                val=fetchInt(inp)
                if val>0x13:
                    #print("err pan",val)
                    val=0x13
                outp += f"$db ${intToHex(val)} ;pan\n"
            elif b == b'\xd8':
                a=fetchInt(inp)
                b=int(fetchInt(inp)/1)
                c=int(fetchInt(inp)/1)
                if a==b==c==0:
                    outp += f"$DF ;vibrato off (000)\n"
                else:
                    outp += f"$de ${intToHex(a)} ${intToHex(a)} ${intToHex(a)};vibrato\n"
            elif b == b'\xd9':
                outp+=f"$EA ${fetchHex(inp)} ;vibr fade\n" #######
            elif b == b'\xda':
                outp+="$DF ;vibr off\n"
            elif b == b'\xd4': #program change

                instr=fetchInt(inp)
                if instr in insReplace.keys():
                    outp += f"@{insReplace[instr]} \n"
                else:
                    outp+=f"@{instr+30} \n"
                    print("instr not in list")
                actualOctave = -1
                #outp += f"$EE $00 ;reset tune\n"
                #outp += f"$FA $02 $00 ;reset tune\n"
                #outp += f"$F4 $09 ;reset inst\n"
            elif b == b'\xe0':
                outp+="\n$FA $02 "
                outp+=f"${fetchHex(inp)} ;transpose ch\n"
                actualOctave=-1
            elif b == b'\xe9':
                outp+=f"$EE ${fetchHex(inp)} ;fine tune\n"
            elif b == b'\xf9': #loop
                if fetchInt(inp)==0:
                    inp.seek(1,1)
                else:
                    inp.seek(2,1)
                outp+=" ;loop\n"
            elif b in [b'\xf4',b'\x00']: #end
                if subPattern:
                    outp2=chunkLeft+"["+outp+"] \n"+chunkRight
                    outp=outp2
                else:
                    outp+=" ;end\nq11 v1 [a1]127 ;(prevent reset)\n"
                break
            elif b == b'\xd1':  # rest
                outp+=f"r{durationStr} "
            elif b == b'\xd2':  #slur on, (bend)
                outp+=f"&"
            elif b == b'\xd3':  #slur off
                outp+=f""
            elif b == b'\xd0':  # tie
                outp+=f"^{durationStr}"
            elif b == b'\xe1':
                outp += f"$e5 ${fetchHex(inp)} ${intToHex(fetchInt(inp)/4)} ${intToHex(fetchInt(inp)/4)};tremolo\n"
            elif b == b'\xe2':
                outp += f"$e5 $00 $00 $00;tremolo off\n"
            elif b == b'\xe6':
                outp += f"$eb ${fetchHex(inp)} ${fetchHex(inp)} ${intToHex(fetchInt(inp)/3)};glisando beta\n"
            elif b == b'\xe8':
                outp += f"$eb $81 $00 $00 ;gliss off\n"
            else:
                input("err")
        return outp

    for ix,track in enumerate(tracks):
        outp+=f"\n#{ix}\nq7a\nt31\n@30\n$F4 $08 ;Louder\n$EF $ff $68 $68 ; fixed echo\n;$fa $03 $8f ;amplify?\n"
        outp=scan(track,outp, False)
    for callPattern in subPatternIds:
        outp=scan(callPattern,outp, True)
    ff=open("C:/Users/int/Documents/emu/SPC/AMK/AddmusicK_1.0.6/music/songg.txt", "w")
    ff.write(outp)
    ff.close()


if __name__ == '__main__':
    spc()

