'''
    Simple socket server using threads
    Credit to http://www.binarytides.com/python-socket-server-code-example/
'''

import socket, sys, threading, ssl
from Crypto.PublicKey import RSA
from Crypto.Random import random
from phe.paillier import PaillierPublicKey
from phe.util import powmod

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 8443 # Arbitrary non-privileged port
RSA_private_key = RSA.construct((
    int('3286263872074415988522731415732565023312391530808916640547945962451032839260032818752406195649382925'
        '5841707306963263944377173403241377917291058133635145296746759541988036065564512765895534762510687701'
        '3057443202332373543498990044331157492829860958738717106705881273923453962522669714506317007005895148'
        '0123315418638721207351019650573956003080466565080337749749013413154849856919689441467669745180356224'
        '3748850604232331340511453053595728950867177885893419756755583260713280775148288207232646190641638476'
        '2865026106742545012973705428444737625665832339539991816576370873289393586156110119028881256879626602'
        '4666454051777956259496486109413504774033505990964594784984752008703224978055936257808192299334692169'
        '6507236932427259974879490356859054497447834471273122930324737965380134373361037131766966503795655903'
        '5917025800410488630756760950980868540197155188855860610741030280367298069541002364433391490995746322'
        '7829692251765684847376359'),
    65537,
    int('2551860089929949556310333467782259892906158618709989422068839250730053438863273115631302984616212925'
        '0027317798475173800956692122989410006391187260308317123102054409742788705809597924366230672733439245'
        '1157458260370429253737691721410149014565885744711720894721592442608579819136383789934555728878908249'
        '9579712909805806810859525779900807100611380196888833306719517854171894717007185488590127424233234792'
        '7836531365488007907746286179570933091819606478645681444696101223353187502215357659600425170593733567'
        '9445311160198997506914566367959969235038246679656180752822248531349376830346417715790054689766737904'
        '1030956966577996172683180651220352959735643404730946902507855300809542566905922596039103172398584256'
        '8793638430610805913140321995134294426681882575147027690679406985757844137410302240078831521819064428'
        '8721113816142169481648468210865331742566576199131154430921700076869735014521956456473644980519639360'
        '5180284853430335921058561'),
    int('1755499665120124930737603604357090152645904956579547577506077857311381971625886381780495220891889312'
        '1027852643142428852819253382292487376565218505471632225498569404342038529362934239443434755764297902'
        '4296738918426560298247068437194383672335526007806042214363436095667736577222235859023017367853802518'
        '9182357174846625633325436331637696048782428422636854955793992154879710533803832607051210432790696863'
        '061766016057232162558670842672792786382176458853266584196452737'),
    int('1871982055803778392476802740345788758859696561585211055384725016851434368935520998885418713898088559'
        '8418663282389899893379025256053425211917863903290311897594491856834816788774485793876862964078700211'
        '5051595425860113579097652652381289438357115345852014278975683760722548127064999055942330089512549084'
        '3457104787310253898939023613930692662609946992238109343510216184595026872508990430490517011040610502'
        '496065494899574677755032259109437651483551873070754235640245607'),
    int('8890019373497156577506573854692757910861682878751666399881268812211327768889285942922917822427406171'
        '1374084535302327665620874750481886059863738167654613913302052224437095881661430248867369722480906681'
        '0293579420608981080797910712789594734623519152297342857449149250317462819509862326203278505821528945'
        '6448968243743443665102431436949177200582903936634957540698176693179452224130375241137422201752548805'
        '38484129753291039384174315026630418515764098957297791847701740'))
)
public_key = PaillierPublicKey(
    int('1484838658248464064259856757081154421171196989150622299748222043593445654503905553445414915359609687'
    '77035409413270882739651258158816563585214558468913443613231772079652558633998048113787675894701782805516'
    '041546348825706150790878817148626225214317380324006002845687798158170472767179664512573569011721121619210'),
    int('1484838658248464064259856757081154421171196989150622299748222043593445654503905553445414915359609687'
        '7703540941327088273965125815881656358521455846891344361323177207965255863399804811378767589470178280'
        '5516041546348825706150790878817148626225214317380324006002845687798158170472767179664512573569011721'
        '121619209')
)

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="server-cert.pem", keyfile="server-key.pem")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')

#Bind socket to local host and port
try:
    sock.bind((HOST, PORT))
except socket.error as msg:
    print('Bind failed. Error Code : ' + str(msg.errno) + ' Message ' + msg.strerror)
    sys.exit()

print('Socket bind complete')

#Start listening on socket
sock.listen(10)
print('Socket now listening')

#Function for handling connections. This will be used to create threads
def handle_client(conn):
    #Sending message to connected client
    #conn.send('Welcome to the server. Type something and hit enter\n'.encode('ASCII')) #send only takes string
    #infinite loop so that function do not terminate and thread do not end.
    while True:

        #Receiving blinded message from client
        data = conn.recv(1024)
        print(sys.getsizeof(data), data)
        if not data:
            break

        #determine if ZKP was sent or blind signature
        print("Data: ",data)

        try:
            print("Data decoded: ",data.decode('ascii'))
            if data.decode('ascii') == "ZKP START":
                print("here...")
                #start ZKP
                for i in range(1,5):
                    successful = False #used to control if the multiplicative inverse of x^e does not exist, then repeat the round
                    while not successful:
                        #wait for u
                        c = conn.recv(2049)
                        print("C data: ",c)
                        c = int(c.decode('ascii'))
                        print("Received c: ", c)
                        u = conn.recv(2048)
                        u = int(u.decode('ascii'))
                        print("Received u: ", u)
                        A = random.randint(3,20)
                        e = random.randint(0,A)
                        print("e: ",e)
                        conn.send(bytes(str(e),'ascii'))
                        wn = conn.recv(2048)
                        wn = wn.decode('ascii')
                        if wn != "restart":
                            wn = int(wn)
                            print("wn: ", wn)
                            v = conn.recv(2048)
                            v = int(v.decode('ascii'))
                            print("v: ", v)
                            gv = powmod(public_key.g, v, public_key.nsquare)
                            ce = powmod(c,e,public_key.nsquare)
                            check = (gv*ce*wn) % public_key.nsquare
                            print("N2: ", public_key.nsquare)
                            print("Check: ", check)
                            print("u: ", u)
                            if check == u:
                                conn.send(bytes("PASS ROUND",'ascii'))
                                successful = True
                            elif check == "Invalid":
                                conn.send(bytes("REPEAT ROUND", 'ascii'))
                            else:
                                conn.send(bytes("FAILED ROUND", 'ascii'))
                                successful = True
                        else:
                            print("Retrying with new s and e... no inverse to w.")
        except UnicodeDecodeError:
            print("there...")
            #print(type(data),data.decode('ascii'),data)
            #calculate signature
            msg_blinded_signature = RSA_private_key.sign(data, 0)
            print(msg_blinded_signature[0])
            print(type(msg_blinded_signature[0]))
            #send the signature, second element is always None
            conn.send(bytes(str(msg_blinded_signature[0]),'ascii'))
        except ValueError:
            pass

#now keep talking with the client
while 1:
    #wait to accept a connection - blocking call
    conn, addr = sock.accept()
    connstream = context.wrap_socket(conn, server_side=True)

    print('Connected with ' + addr[0] + ':' + str(addr[1]))

    try:
        handle_client(connstream)
    finally:
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()

sock.close()
