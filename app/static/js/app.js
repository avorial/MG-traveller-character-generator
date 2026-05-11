/* ============================================================
   TRAVELLER — Character Generation Terminal
   Client-side phase controller
   ============================================================ */

// ------------------------------------------------------------
// Boot data + state
// ------------------------------------------------------------

// ============================================================
// NAME GENERATOR  (ported from Corsair WordGen by J. Robinson / D. Burden)
// ============================================================

const _NL = {
  // basicSyls / alternateSyls: cumulative weights out of 36
  // initConst / finalConst / vowels: cumulative weights out of 216
  1:  { // Trokh (Aslan)
    b:[["v",13],["cv",22],["vc",30],["cvc",36]],
    a:[["v",15],["vc",36]],
    i:[["f",12],["ft",22],["h",40],["hf",45],["hk",57],["hl",65],["hr",72],["ht",84],["hw",89],["k",106],["kh",121],["kht",132],["kt",142],["l",147],["r",154],["s",164],["st",171],["t",191],["tl",196],["tr",201],["w",216]],
    f:[["h",46],["kh",64],["l",96],["lr",110],["r",133],["rl",151],["s",175],["w",199],["'",216]],
    v:[["a",41],["ai",52],["ao",60],["au",64],["e",90],["ea",114],["ei",127],["i",143],["iy",155],["o",163],["oa",167],["oi",175],["ou",180],["u",184],["ua",188],["ui",195],["ya",200],["ye",208],["yo",212],["yu",216]]
  },
  2:  { // Te-Zlodh (Darrian)
    b:[["cvc",27],["cv",36]],
    a:[["vc",27],["v",36]],
    i:[["b",17],["d",39],["g",46],["p",58],["t",66],["th",73],["k",78],["m",88],["n",110],["z",132],["l",142],["r",156],["y",162],["zb",166],["zd",171],["zg",174],["zl",177],["mb",182],["nd",187],["ngg",190],["ry",195],["ly",198],["ny",204],["lz",209],["ld",216]],
    f:[["bh",9],["dh",18],["gh",24],["p",30],["t",36],["k",45],["n",66],["ng",78],["l",109],["r",138],["s",156],["m",171],["mb",177],["nd",183],["ngg",186],["yr",192],["ly",195],["ny",198],["lbh",201],["lz",207],["ld",216]],
    v:[["a",47],["e",94],["eh",123],["i",152],["ih",175],["o",204],["u",216]]
  },
  3:  { // Oynprith (Droyne)
    b:[["v",7],["cv",18],["vc",29],["cvc",36]],
    a:[["v",6],["cv",12],["vc",18],["cvc",36]],
    i:[["b",8],["br",12],["d",24],["dr",29],["f",42],["h",55],["k",68],["kr",71],["l",20],["m",94],["n",108],["p",120],["pr",122],["r",133],["s",157],["ss",167],["st",170],["t",180],["th",186],["tr",189],["ts",198],["tw",207],["v",216]],
    f:[["b",6],["d",17],["f",22],["h",28],["k",36],["l",40],["lb",42],["ld",49],["lk",53],["lm",56],["ln",57],["lp",58],["ls",60],["lt",62],["m",73],["n",80],["p",92],["r",101],["rd",104],["rf",106],["rk",111],["rm",115],["rn",118],["rp",119],["rs",123],["rt",128],["rv",130],["s",153],["sk",160],["ss",167],["st",172],["t",184],["th",190],["ts",200],["v",204],["x",216]],
    v:[["a",24],["ay",42],["e",84],["i",114],["o",138],["oy",150],["u",189],["ya",198],["yo",205],["yu",216]]
  },
  4:  { // Ithklur
    b:[["cv",36]],
    a:[["cv",36]],
    i:[["d",12],["f",24],["g",30],["gh",36],["h",42],["hz",48],["j",54],["jj",60],["jz",66],["k",75],["kk",80],["kl",85],["ks",90],["kz",95],["l",102],["ll",105],["mm",111],["n",117],["q",126],["r",130],["rr",136],["rs",139],["rz",142],["s",148],["ss",156],["th",165],["tr",170],["x",183],["xx",195],["z",201],["zz",207],["'",216]],
    f:[["d",15],["f",24],["g",30],["gh",42],["h",48],["hz",54],["j",60],["jj",63],["jz",69],["k",81],["kk",90],["ks",99],["kz",108],["l",116],["ll",120],["m",126],["n",132],["q",141],["r",150],["rr",156],["rs",162],["rz",168],["ss",180],["th",186],["x",192],["xx",198],["z",207],["zz",216]],
    v:[["a",30],["aa",36],["ae",42],["e",66],["ee",72],["i",102],["ii",117],["o",144],["ou",150],["u",174],["ue",186],["uu",196],["y",201],["yu",204],["yy",207],["'t'",216]]
  },
  5:  { // K'Kree
    b:[["v",6],["cv",21],["vc",27],["cvc",36]],
    a:[["cv",18],["vc",23],["cvc",36]],
    i:[["b",2],["g",10],["gh",24],["gn",33],["gr",37],["gz",39],["hk",43],["k",96],["kr",118],["kt",120],["l",131],["m",135],["mb",137],["n",147],["p",149],["r",175],["rr",182],["t",197],["tr",201],["x",210],["xk",212],["xr",214],["xt",216]],
    f:[["b",5],["g",11],["d",15],["gh",20],["gr",25],["k",57],["kr",72],["l",82],["m",87],["n",97],["ng",112],["p",117],["r",159],["rr",181],["t",196],["x",211],["xk",216]],
    v:[["a",68],["aa",75],["e",86],["ee",100],["i",122],["ii",129],["o",133],["oo",140],["u",162],["uu",169],["'",197],["!",208],["!!",212],["!'",216]]
  },
  6:  { // Gvegh (Vargr)
    b:[["v",4],["vc",18],["cv",22],["cvc",36]],
    a:[["cv",18],["cvc",36]],
    i:[["d",9],["dh",18],["dz",23],["f",30],["g",48],["gh",59],["gn",62],["gv",69],["gz",73],["k",91],["kf",96],["kh",107],["kn",113],["ks",120],["l",124],["ll",132],["n",139],["ng",144],["r",155],["rr",163],["s",174],["t",181],["th",190],["ts",194],["v",204],["z",216]],
    f:[["dh",5],["dz",10],["g",25],["gh",35],["ghz",40],["gz",45],["k",55],["kh",65],["khs",70],["ks",76],["l",86],["ll",91],["n",116],["ng",141],["r",156],["rr",171],["rrg",176],["rrgh",181],["rs",186],["rz",191],["s",196],["th",201],["ts",106],["z",216]],
    v:[["a",42],["ae",76],["e",92],["i",102],["o",136],["oe",152],["ou",168],["u",192],["ue",216]]
  },
  7:  { // Vilani
    b:[["v",6],["cv",21],["vc",29],["cvc",36]],
    a:[["cv",21],["cvc",36]],
    i:[["k",39],["g",78],["m",99],["d",120],["l",141],["sh",162],["kh",180],["n",190],["s",200],["p",204],["b",208],["z",212],["r",216]],
    f:[["r",75],["n",102],["m",139],["sh",165],["g",180],["s",191],["d",204],["p",210],["k",216]],
    v:[["a",67],["e",84],["i",143],["u",183],["aa",192],["ii",208],["uu",216]]
  },
  8:  { // Zhodani
    b:[["v",3],["cv",6],["vc",15],["cvc",36]],
    a:[["v",6],["cv",12],["vc",18],["cvc",36]],
    i:[["b",6],["bl",8],["br",13],["ch",25],["cht",32],["d",41],["dl",48],["dr",53],["f",58],["fl",61],["fr",64],["j",71],["jd",76],["k",81],["kl",83],["kr",85],["l",88],["m",90],["n",98],["p",105],["pl",112],["pr",115],["q",117],["ql",119],["qr",121],["r",126],["s",133],["sh",140],["sht",147],["t",152],["st",159],["tl",169],["ts",172],["v",177],["vl",179],["vr",181],["y",184],["z",189],["zd",199],["zh",206],["zhd",216]],
    f:[["b",2],["bl",9],["br",16],["ch",21],["d",25],["dl",32],["dr",39],["f",44],["fl",49],["fr",54],["j",58],["k",60],["kl",64],["kr",66],["l",78],["m",80],["n",82],["nch",89],["nj",94],["ns",99],["nsh",106],["nt",110],["nts",114],["nz",119],["nzh",126],["p",128],["pl",135],["pr",142],["q",144],["ql",146],["qr",148],["r",153],["sh",160],["t",164],["ts",171],["tl",180],["v",185],["vl",189],["vr",194],["z",203],["zh",210],["'",216]],
    v:[["a",43],["e",105],["i",140],["ia",168],["ie",192],["o",210],["r",216]]
  },
  9:  { // Gurvin (Hiver)
    b:[["cv",12],["vc",24],["cvc",36]],
    a:[["v",6],["cv",8],["vc",22],["cvc",36]],
    i:[["bl",6],["c",12],["d",24],["dr",30],["f",36],["g",54],["gl",58],["h",62],["k",86],["kl",90],["l",102],["ld",105],["ly",108],["m",116],["n",138],["p",150],["phl",158],["q",162],["r",171],["s",174],["sl",180],["sp",186],["t",192],["th",195],["tr",202],["v",206],["w",208],["wr",214],["z",216]],
    f:[["c",12],["ck",18],["d",21],["f",27],["ft",30],["g",33],["h",36],["k",39],["l",57],["ld",60],["m",66],["n",102],["nsk",105],["nt",108],["p",114],["phl",117],["q",126],["r",149],["rk",151],["rn",157],["rt",159],["s",162],["sk",174],["st",177],["t",192],["th",195],["v",198],["x",216]],
    v:[["a",72],["e",108],["i",138],["o",168],["oo",180],["u",204],["ua",212],["y",216]]
  },
  10: { // Ael Yael
    b:[["vc",3],["cv",30],["cvc",36]],
    a:[["cv",36]],
    i:[["h",54],["j",72],["l",90],["y",216]],
    f:[["l",216]],
    v:[["ae",66],["a",116],["e",166],["i",200],["u",216]]
  },
  11: { // Neo-Icelandic (Sword Worlds)
    b:[["v",1],["vc",6],["cv",14],["cvc",36]],
    a:[["vc",3],["cv",14],["cvc",36]],
    i:[["b",12],["bl",14],["br",16],["d",31],["f",45],["fl",46],["fr",47],["g",51],["gj",52],["gr",54],["h",61],["j",67],["k",78],["kj",79],["kl",81],["l",97],["m",108],["n",120],["p",128],["pr",129],["r",145],["s",160],["sj",161],["sk",164],["sl",166],["sm",167],["sn",168],["sp",170],["st",175],["sv",177],["t",196],["tr",200],["v",216]],
    f:[["b",3],["d",12],["dd",13],["f",15],["g",27],["gg",29],["gn",30],["gs",31],["gt",32],["k",44],["kk",49],["ks",50],["kt",51],["l",72],["ld",73],["ll",74],["lm",75],["lp",76],["lt",78],["lv",79],["m",85],["n",110],["nd",112],["ndt",113],["ng",126],["nn",131],["nsk",132],["nt",134],["p",139],["psk",140],["r",170],["rd",173],["rk",174],["rsk",175],["rt",177],["rv",178],["s",182],["sk",184],["sp",185],["st",187],["t",210],["tt",215],["v",216]],
    v:[["au",1],["ie",2],["oy",4],["o",11],["ae",13],["a",18],["a",60],["e",126],["i",168],["o",193],["u",207],["y",216]]
  },
  12: { // Bwap
    b:[["cv",13],["cvc",25],["vc",34],["v",36]],
    a:[["cv",13],["cvc",25],["vc",34],["v",36]],
    i:[["p",42],["w",108],["s",132],["t",156],["d",162],["k",192],["b",207],["f",216]],
    f:[["-",72],["b",150],["s",174],["t",186],["th",198],["k",204],["r",210],["p",216]],
    v:[["a",132],["e",204],["o",216]]
  },
  16: { // Galanglic
    b:[["cv",15],["cvc",29],["vc",35],["cvc",36]],
    a:[["cv",15],["cvc",29],["vc",35],["cvc",36]],
    i:[["b",5],["c",15],["ch",18],["d",23],["f",33],["fr",36],["g",48],["gh",51],["h",59],["j",64],["k",69],["kn",72],["l",80],["m",92],["n",107],["p",120],["phl",121],["q",125],["r",140],["s",152],["sh",155],["st",158],["t",176],["th",184],["tr",187],["v",192],["w",200],["wh",203],["y",211],["z",216]],
    f:[["c",10],["ch",15],["d",29],["k",34],["l",66],["ll",70],["m",80],["n",138],["nd",142],["p",151],["r",178],["rb",182],["rs",186],["rt",190],["s",200],["st",205],["tw",209],["v",213],["z",216]],
    v:[["a",38],["ae",41],["e",111],["i",145],["ie",148],["io",151],["o",187],["ou",194],["u",206],["ua",209],["y",216]]
  }
};

// Solomani real-world name pools (forebears.io)
const _SOL_FIRST = ["Maria","Mohammed","Jose","Wei","Ahmed","Yan","Ali","John","David","Li","Abdul","Ana","Michael","Juan","Anna","Mary","Jean","Robert","Daniel","Luis","Carlos","James","Antonio","Joseph","Elena","Francisco","Marie","Ibrahim","Peter","Fatima","Richard","Paul","Olga","Pedro","William","Rosa","Thomas","Jorge","Elizabeth","Sergey","Ram","Patricia","Hassan","Anita","Manuel","Victor","Sandra","Miguel","Emmanuel","Samuel","Charles","Sarah","Mario","Mark","Martin","Patrick","Natalya","Ahmad","Martha","Sunita","Andrea","Christine","Irina","Laura","Linda","Marina","Carmen","Vladimir","Barbara","Angela","George","Roberto","Ivan","Alexander","Ekaterina","Jesus","Susan","Sara","Noor","Eric","Fernando","Esther","Diana","Mahmoud","Chao","Nancy","Musa","Omar","Jennifer","Claudia","Maryam","Gloria","Ruth","Teresa","Sanjay","Francis","Amina","Denis","Stephen","Gabriel","Andrew","Eduardo","Abdullah","Grace","Mei","Rafael","Ricardo","Christian","Steven","Frank","Karen","Brian","Christopher","Rajesh","Mustafa","Eva","Monica","Oscar","Andre","Catherine","Ramesh","Sonia","Anthony","Manoj","Ashok","Rose","Alberto","Rekha","Aung","Alex","Suresh","Anil","Julio","Simon","Paulo","Juana","Irene","Adam","Kevin","Vijay","Mehmet","Angel","Edward","Julia","Victoria","Ronald","Lakshmi","Francisca","Veronica","Roman","Ismail","Margaret","Luz","Anne","Silvia","Kamal","Raju","Sergio","Walter","Lisa","Marta","Marco","Albert","Alice","Isabel","Zainab","Michelle","Michel","Pierre","Felix","Hector","Jan","Roger","Joyce","Joel","Jessica","Lucia","Pavel","Nadia","Benjamin","Rebecca","Julie","Vera","Vinod","Khalid","Ramon","Janet","Sharon","Jane","Abubakar","Aisha","Jonathan","Paula","Bruno","Monika","Mamadou","Judith","Kenneth","Chris","Helen","Nikolay","Marcos","Norma","Anton","Raul","Cristina","Henry","Antonia","Betty","Alejandro","Nelson","Igor","Evgeniy","Adriana","Amir","Pablo","Raj","Regina","Brenda","Hussein","Mikhail","Jaime","Nicole","Giuseppe","Dinesh","Bernard","Gary","Javier","Hasan","Moses","Agnes","Cesar","Usha","Alfredo","Kiran","Dennis","Khaled","Carol","Rani","Yusuf","Rakesh","Isaac","Luiz","Josephine","Krishna","Raymond","Erika","Blanca","Deborah","Amanda","Natalia","Gladys","Florence","Usman","Donald","Maya","Mahdi","Khadija","Valentina","Ruben","Jason","Doris","Rene","Cecilia","Umar","Cynthia","Gustavo","Kim","Lucas","Moussa","Nawaz","Amit","Mona","Dilip","Caroline","Tun","Claude","Elisabeth","Beatrice","Edwin","Kristina","Scott","Christina","Ajay","Alina","Denise","Matthew","Daniela","Joan","Leonardo","Ravi","Virginia","Hamid","Alain","Alicia","Mohan","Hans","Ann","Nicolas","Felipe","Amal","Donna","Dina","Hugo","Yolanda","Beatriz","Mukesh","Brigitte","Evelyn","Emma","Kenji","Galina","Diego","Viktor","Arun","Alexandra","Alfred","Louis","Armando","Vincent","Edith","Alan","Hiroshi","Gabriela","Rachel","Adrian","Mira","Shankar","Carla","Miriam","Gopal","Amy","Mercy","Timothy","Irma","Marcelo","Rodrigo","Pamela","Agus","Jerry","Jacques","Jeanne","Joy","Ganesh","Ingrid","Juliana","Mahesh","Nina","Rahul","Petra","Nikita","Yasmin","Melissa","Wilson","Jeffrey","Giovanni","Larry","Elias","Kelly","Osman","Piotr","Philip","Raja","Dorothy","Sultan","Ernesto","Oleg","Joe","Ruslan","Diane","Andres","Shirley","Justin","Enrique","Mariana","Monique","Vanessa","Prakash","Dan","Dominique","Susana","Annie","Douglas","Ahmet","Bashir","Elsa","Samir","Abbas","Aya","Chunyan","Guillermo","Luisa","Karin","Andreas","Leila","Helena","Philippe","Vicente","Konstantin","Tania","Pascal","Aziz","Martina","Fred","Tamara","Tony","Ryan","Lucy","Surendra","Marc","Sabina","Guadalupe","Salim","Amar","Lydia","Mahendra","Joshua","Lee","Ayesha","Karina","Salah","Ilya","Josef","Leticia","Michele","Nasir","Josefa","Narayan","Kavita","Pramod","Sofia","Alexey","Hossein","Tina","Claudio","Nathalie","Arthur","Sam","Karl","Mercedes","Shigeru","Kathleen","Farida","Marcel","Guohua","Francesco","Nurul","Sayed","Jay","Abraham","Nour","Imran","Sai","Iman","Jamal","Wolfgang","Manuela","Raquel","Artur","Uma","Louise","Nabil","Hilda","Abdoulaye","Wendy","Ian","Stella","Elvira","Valerie","Subhash","Sylvia","Jeff","Carolina","Tomasz","Gilbert","Gerald","Francois","Rodolfo","Melanie","Ashraf","Gerardo","Sheila","Rana","Kalpana","Simone","Orlando","Petr","Arif","Eunice","Farzana","Angelo","Amadou","Robin","Rashid","Abel","Ranjit","Alexandre","Jack","Fabio","Prem","Mustapha","Sabine","Aida","Klaus","Ran","Heba","Shah","Terry","Yvonne","Lawrence","Lal","Therese","Jenny","Mike","Nada","Vasylyi","Manfred","Marcia","Keith","Guy","Umesh","Solomon","Jimmy","Paulina","Aminata","Nora","Ravindra","Sophie","Joanna","Sylvie","Raimundo","Laila","Pankaj","Reza","Roland","Emily","Habib","Angelica","Liliana","Isabelle","Tim","Durga","Naresh","Babu","Nguyen","Arjun","Shyam","Alaa","Herbert","Olivier","Kseniya","Hanan","Amin","Renu","Masako","Priyanka","Nasreen","Salvador","Martine","Judy","Maha","Nicholas","Theresa","Shahid","Stefan","Marcin","Sebastian","Josefina","Gilberto","Ida","Artyom","Rosario","Roy","Pramila","Kathy","Rabia","Nestor","Paola","Ernest","Yousef","Luciano","Faisal","Dmitry","Alma","Yanyan","Dolores","Leonard","Marilyn","Bharat","Katarzyna","Sabrina","Arturo","Gerhard","Cristian","Joaquim","Julius","Maurice","Kirill","Rosemary","Elaine","Marianne","Cheryl","Helga","Faith","Heather","Heinz","Sandeep","Satish","Ellen","Sangeeta","Bernadette","Noel","Deepak","Christophe","Ken","Kailash","Lorena","Samia","Issa","Gregory","Lila","Chantal","Thierry"];
const _SOL_LAST = ["Wang","Li","Zhang","Chen","Liu","Yang","Huang","Singh","Wu","Kumar","Xu","Ali","Zhao","Zhou","Nguyen","Khan","Ma","Lu","Zhu","Sun","Yu","Lin","Kim","He","Hu","Jiang","Guo","Ahmed","Luo","Devi","Garcia","Mohammad","Tan","Deng","Bai","Ahmad","Yan","Kaur","Feng","Hernandez","Rodriguez","Cao","Lopez","Hassan","Hussain","Gonzalez","Martinez","Ibrahim","Peng","Cai","Xiao","Tran","Pan","dos Santos","Cheng","Yuan","Rahman","Yadav","Su","Perez","Le","Fan","Dong","Ye","Ram","Tian","Fu","Hossain","Kumari","Sanchez","Du","Pereira","Yao","Zhong","Jin","Pak","Ding","Mohammed","Lal","Yin","Bibi","Silva","Muhammad","Ren","Ferreira","Liao","Mandal","Cui","Begum","Fang","Sharma","Alves","Shah","Ray","Qiu","Meng","Ramirez","Mondal","Dai","Kang","Patel","Wen","Gu","Gomez","Pham","Jia","Sah","Xia","Hong","Abdul","Rodrigues","Smith","Santos","Diaz","Hou","Hasan","Xiong","Zou","Alam","Prasad","de Oliveira","Qin","Choe","Ji","Uddin","Musa","Gong","Ghosh","Chang","Flores","Diallo","Gomes","Xue","Lei","Patil","Torres","de Souza","Qi","Lai","Cruz","Long","Ramos","Hussein","Fernandez","Duan","Shaikh","Xiang","Pal","Morales","Wan","Johnson","Reyes","Abdullahi","Tao","Gupta","Jimenez","Mao","Biswas","Kong","Hoang","Williams","Abubakar","Abbas","Sahu","Gutierrez","Chong","Hao","Shao","Saha","Guan","Mo","Ruiz","Oliveira","Qian","Roy","Saleh","Abdullah","Lan","Sarkar","Sani","Castillo","Alvarez","Brown","Martin","Jones","Mendoza","Romero","Iqbal","Qu","Rana","Castro","Ansari","Usman","Traore","Bao","Rojas","Mahmoud","Martins","Ortiz","Vu","Moreno","Malik","Ribeiro","Lee","Ullah","Ismail","Fernandes","Rani","Thomas","John","Phan","Rivera","Chu","Adamu","Tong","Vargas","Niu","Xing","Joseph","Lopes","Cho","Osman","Umar","Pang","Rathod","Jadhav","Bui","Chand","Coulibaly","Barman","Soares","Sato","Khaled","Chan","Saeed","Mishra","Herrera","Thakur","Barbosa","Behera","Adam","Lima","Sultana","Suzuki","Medina","Ho","Bano","Costa","Aguilar","Dias","Dang","Paswan","Qiao","Abdi","Miller","Chowdhury","Camara","Omar","Akhtar","Ouedraogo","Shen","Gul","Mai","Vieira","Davis","Wilson","Mendez","Batista","Souza","Sardar","Paul","Ha","Vazquez","Thakor","Miranda","Vasquez","Haque","Haji","Chauhan","Amin","Huynh","Sayed","Rashid","Pawar","Chavez","Shang","Gan","Rai","Pradhan","Naik","Karim","James","Taylor","Geng","Hossen","de Sousa","Jahan","Salazar","Yun","da Costa","Kone","Tanaka","Moussa","Mustafa","Guzman","Jiao","Rao","Juma","Watanabe","Anderson","Moreira","Ilunga","Takahashi","Sheikh","Shinde","Hamid","Bello","Aliyu","Akhter","Nath","Mendes","Suarez","Jackson","Aziz","Ortega","Cardoso","Molla","Garba","Campos","Pinto","Ashraf","Khalil","Jean","Delgado","Noor","Truong","Nunes","Miah","Anwar","Almeida","Molina","Dominguez","Banda","Chandra","Thompson","Contreras","Hua","Aslam","de Lima","Araujo","Rocha","Shaik","Ivanova","Raut","Ruan","Guerrero","David","Peter","Soto","Acosta","Ivanov","Jha","Santana","Bala","White","Tesfaye","Moore","Sultan","Mejia","Solomon","Ghulam","Zaman","Ouattara","Issa","Yamamoto","Lam","Navarro","Nakamura","Machado","Andrade","Bauri","Said","Simon","Raj","Barry","Ramadan","do Nascimento","Vega","Saad","Alvarado","Patra","Espinoza","Abdel","Cabrera","Rios","Murmu","Mehmood","Salem","Teixeira","Leon","Marques","Mostafa","Solanki","Harris","Kobayashi","Huo","Xin","Schmidt","Bah","Pandey","Idris","Dutta","Sheng","Prakash","Pei","Rosa","Kato","Aung","Saito","May","Gonzales","Francisco","Awad","Correa","Sawadogo","Perera","Santiago","de Almeida","Hwang","Pandit","Toure","Ko","Chai","Khin","Munda","Robinson","Suleiman","Chakraborty","Sharif","Juarez","Patal","Kamal","Jain","Phiri","Salah","Walker","Akbar","Clark","Lewis","Diarra","Avila","Chaudhary","Franco","Ndiaye","Arias","Pathan","Charles","Luna","Pacheco","Samuel","Marquez","Carvalho","Salim","Qasim","Hamza","Emmanuel","Rehman","Bautista","Nascimento","Hoque","Fernando","Mahmud","Salman","Kabir","Kamble","Bashir","Manjhi","Sousa","Fuentes","Domingos","Marin","Cisse","Adams","Keita","Hall","King","Abdalla","Habib","Young","Monteiro","Debnath","Daniel","Getachew","Husain","Jena","Wright","Makavan","Kaya","Thapa","Yoshida","Giri","Yahaya","Akram","Mora","Kazem","Saleem","Siddique","Baba","Yamada","Sandoval","Velasquez","Estrada","Abu","Green","Scott","Roberts","Rivas","Isah","Escobar","Duran","Dey","Tadesse","Nisha","Benitez","Cortes","Lawal","Dao","Kwon","Abebe","Mahamat","Evans","Kamara","Campbell","Mir","Girma","Win","Khalid","Borges","Lim","Yakubu","Pierre","Jassim","Diop","Reddy","Quispe","Gayakwad","Sinha","Yousef","de La Cruz","Lara","Hill","Valencia","Shaw","Felix","Taha","Rasool","Aguirre","Aminu","Sadiq","Maldonado","Calderon","Nelson","Wong","Valdez","Karmakar","Baker","Parveen","Koffi","Rahim","Correia","Guerra","Trinh","Varma","Arif","Jana","George","Vera","Demir","Cardenas","Mun","Sosa","Kouassi","Haider","Serrano","Schneider","Bag","Lang","Meyer","Parvin","Figueroa","Hadi","Magar","Villanueva","Padilla","Ayala","Nasser","Edwards","Pineda","Rosales","Zin","Hosseini","Kadam","Blanco","Mansour","Barik","Rahaman","Sasaki","Oraon","Hayat","Dembele","Brito","Carrillo","Babu","Mitchell","Tudu","Al Numan","Velazquez","Matsumoto","Michael","Amir","Setiawan","Khalaf","Adhikari","Jan","de Araujo","Tiwari","Javed","Camacho","Eze","Bhagat","Morris","Gil","Sylla","Yamaguchi","Latif","Sarker","Elias","Mamani","Sidibe","Turner","Phillips","Raza","Kebede","Yousuf","Solis","Carter","Mori","Murphy","Nasir","Inoue","Kouadio","Mallik","Salas","Bravo","de Carvalho","Parra","Stewart","Tavares","Afzal","Kanwar","Verma","Henrique","Kouame","Collins","Cooper","Antonio","Quintero","Bekele","Ahmadi","Nair","Kelly","Nahar","Pinheiro","Bux","Adel","Wagner","dela Cruz","Akpan","Weber","Dube","Salam","Gamal","Asif","Morgan","Luong","Sheik","Barros","Pedro","Palacios","Parker","Abe","Kimura","Bezerra","Cortez","Doan","Shehu","Bahadur","Joshi","Mane","Farah","Ahamed","Barrios","Balde","Amadi","Bera","Bell","Nabi","Gabriel","Hamad","Shankar","Sen","Lucas","Basumatary","Fischer","Robles","Arshad","Hailu","Kouakou","Farooq","Oumarou","Fofana","Jamal","Hansen","Wood","Aden","Pires","Alemayehu","Peralta","Espinosa","Dlamini","Meza","Hayashi","Petrov","Hamed","Shimizu","Mensah","Jang","Panda","Moses","Saidi","Tahir","Sahani","Halder","Cook","Moyo","Watson","Hughes","Ochoa","Paredes","Mahmood","Lozano","Hameed","Conde","Otieno","Mousa","Rogers","Guevara","Osorio","Ward","Salinas","Fonseca","Riaz","Valenzuela","Sulaiman","Thanh","Alonso","da Cruz","Yahya","Gogoi","Saputra","Pramanik","Zapata","Younis","Roman","Francis","Mukherjee","Manna","Freitas","Leal","Vaghel","Shahzad","Abbasi","Petrova","Ndlovu","Bailey","Shafi","Orozco","Banerjee","Ponce","Zamora","Sahoo","Kale","Banza","Coelho","Amadou","Bagdi","Adamou","Narayan","Ono","Ibarra","Caballero","Mercado","Bennett","Montoya","Yar","Aquino","Barrera"];

// Species → language mapping
const _SPECIES_LANG = {
  imperial_human:'solomani', frontier_human:'solomani',
  confederation_human:'solomani', hiver_federation_human:'solomani',
  two_thousand_worlds_human:'solomani', drinax_palace_human:'solomani',
  drinax_wasteland_human:'solomani', asim_human:'solomani',
  human:'solomani', luriani:'vilani', jonkeereen:'solomani',
  sydite:'galanglic', akeed:'galanglic', faar:'galanglic',
  droashav:'galanglic', dolphin:'galanglic', uplifted_orca:'galanglic',
  alpine_caprisap:'galanglic', boar_caprisap:'galanglic',
  capry_big_male:'galanglic', capry_female:'galanglic', capry_small_male:'galanglic',
  solomani_human:'solomani', solomani_mixed:'solomani', solomani_racial:'solomani',
  sword_worlds_human:'icelandic',
  zhodani_human:'zhodani',
  imperial_bwap:'bwap',
  imperial_aslan:'aslan', hierate_aslan:'aslan', aslan:'aslan',
  imperial_vargr:'vargr', extents_vargr:'vargr', vargr:'vargr',
};
const _LANG_ID = { aslan:1, vargr:6, vilani:7, zhodani:8, bwap:12, icelandic:11, galanglic:16 };

function _randLetter(arr) {
  const r = Math.ceil(Math.random() * 216);
  for (const [ch, w] of arr) if (r <= w) return ch;
  return '';
}
function _randSyl(arr) {
  const r = Math.ceil(Math.random() * 36);
  for (const [pat, w] of arr) if (r <= w) return pat;
  return 'cv';
}
function _numSyls(max = 4) {
  let n = 1;
  for (let i = 1; i < max; i++) if (Math.random() < 0.5) n++;
  return n;
}
function _makeSyl(pat, L) {
  let out = '';
  for (const ch of pat) {
    if (ch === 'v') out += _randLetter(L.v);
    else if (ch === 'c') out += _randLetter(pat.indexOf(ch) === 0 ? L.i : L.f);
  }
  return out;
}
function _buildWord(lid, syls) {
  const L = _NL[lid];
  if (!L) return '';
  let pat = _randSyl(L.b);
  let out = '';
  for (let i = 0; i < syls; i++) {
    out += _makeSyl(pat, L);
    pat = pat.endsWith('v') ? _randSyl(L.b) : _randSyl(L.a);
  }
  return out;
}
function _capWord(lid) {
  const w = _buildWord(lid, _numSyls());
  return w ? w[0].toUpperCase() + w.slice(1) : '';
}

function generateSpeciesName(speciesId) {
  const lang = _SPECIES_LANG[speciesId] || 'galanglic';
  if (lang === 'solomani') {
    const fn = _SOL_FIRST[Math.floor(Math.random() * _SOL_FIRST.length * 0.99)];
    const ln = _SOL_LAST[Math.floor(Math.random() * _SOL_LAST.length * 0.99)];
    return `${fn} ${ln}`;
  }
  const lid = _LANG_ID[lang] || 16;
  const r = Math.ceil(Math.random() * 6);
  if (r === 1) return _capWord(lid);
  if (r <= 5) return `${_capWord(lid)} ${_capWord(lid)}`;
  return `${_capWord(lid)} ${_capWord(lid)} ${_capWord(lid)}`;
}

const SPECIES = JSON.parse(document.getElementById('bootstrap-species').textContent);
const CAREERS = JSON.parse(document.getElementById('bootstrap-careers').textContent);
const SKILLS_DATA = JSON.parse(document.getElementById('bootstrap-skills').textContent);
const SOCIETIES = JSON.parse(document.getElementById('bootstrap-societies').textContent);

// Flat list of all skills as "Skill" or "Skill (Speciality)" strings.
const ALL_SKILLS = [
  ...SKILLS_DATA.core,
  ...Object.entries(SKILLS_DATA.speciality).flatMap(([parent, specs]) =>
    specs.map(s => `${parent} (${s})`)
  )
];
const ALL_SKILLS_NO_JOT = ALL_SKILLS.filter(s => s !== 'Jack-of-All-Trades');

// Optional / house-rule extra characteristics
const EXTRA_STATS = [
  { id: 'PSI', label: 'Psychic',   desc: 'Psionic potential' },
  { id: 'WLT', label: 'Wealth',    desc: 'Starting financial fortune' },
  { id: 'LCK', label: 'Luck',      desc: 'Fortune and chance' },
  { id: 'MRL', label: 'Morale',    desc: 'Resolve and spirit' },
  { id: 'STY', label: 'Sanity',    desc: 'Mental stability' },
  { id: 'TER', label: 'Territory', desc: 'Influence and turf' },
];

// Skills that require a specialty when gained at level 1 (MgT 2e cascade skills).
// Maps bare skill name → list of common specialties.
const CASCADE_SKILLS = {
  'Athletics':      ['Dexterity', 'Endurance', 'Strength'],
  'Drive':          ['Hovercraft', 'Mole', 'Track', 'Walker', 'Wheel'],
  'Electronics':    ['Comms', 'Computers', 'Remote Ops', 'Sensors'],
  'Engineer':       ['J-drive', 'Life Support', 'M-drive', 'Power'],
  'Flyer':          ['Airship', 'Grav', 'Ornithopter', 'Rotor', 'Wing'],
  'Gun Combat':     ['Archaic', 'Energy', 'Slug'],
  'Gunner':         ['Capital', 'Ortillery', 'Screen', 'Turret'],
  'Heavy Weapons':  ['Artillery', 'Man Portable', 'Vehicle'],
  'Language':       ['Anglic', 'Bilanidin', 'Oynprith', 'Trokh', 'Zdetl'],
  'Melee':          ['Blade', 'Bludgeon', 'Natural', 'Unarmed'],
  'Pilot':          ['Capital Ships', 'Small Craft', 'Spacecraft'],
  'Science':        ['Archaeology', 'Astronomy', 'Biology', 'Chemistry', 'Cosmology', 'Cybernetics', 'Economics', 'Genetics', 'History', 'Linguistics', 'Philosophy', 'Physics', 'Planetology', 'Psionicology', 'Psychology', 'Robotics', 'Sophontology', 'Xenology'],
  'Seafarer':       ['Ocean Ships', 'Personal', 'Sail', 'Submarine'],
  'Tactics':        ['Military', 'Naval'],
};

const STORAGE_KEY = 'traveller-character-v1';

let SKILL_PACKAGES = {};
let CAREER_DATA = {};  // full career JSON (loaded async in bootstrap)

let character = null;
let uiState = {
  // Transient selections that aren't part of the character yet
  selectedSpecies: null,
  selectedBgSkills: new Set(),
  selectedPreCareerSkills: new Set(),
  selectedCareer: null,
  selectedAssignment: null,
  selectedCoverCareer: null,   // SolSec Secret Agent cover career
  // After-roll dialog state
  lastRoll: null,
  // Stat-swap UI state (characteristics phase)
  swapPick: null,   // which tile the user clicked first (for 2-click swap)
  swapA: 'EDU',     // dropdown A default
  swapB: 'STR',     // dropdown B default
  // Current phase sub-state: 'qualify' | 'assign' | 'train' | 'survive' | 'event' | 'advance' | 'decide' | 'mishap' | 'muster' | 'aging_result'
  subPhase: null,
  pendingAge: false,
  // Aging intercept — set after end-term, cleared once the player clicks CONTINUE
  agingResult: null,          // the aging dict returned by /api/character/end-term
  agingNextAction: null,      // {type:'next_term',careerId,assignmentId} | {type:'muster_out'} | {type:'muster_out_mishap'}
  agingSelectedStats: [],     // player-chosen stats for pending physical reductions [[stat, amount], ...]
  // Anagathics intercept — offered before career selection each term (term 4+)
  anagathicsPhaseDone: false, // true once the player has resolved the anagathics prompt this cycle
  pendingNextTermAction: null, // stores {type:'next_term',...} when continuing same career, awaiting anagathics
  // GM / cheat mode — unlocks direct stat editing, boon rolls, phase skipping.
  gmMode: (localStorage.getItem('traveller_gm_mode') === '1'),
  // Connections step (between muster-out and done).
  connectionsDone: false,
  connections: [],
  // Basic training skills auto-applied at start of first career term.
  basicTrainingSkills: null,
  // Skill package selection (post mustering-out).
  skillPackageApplied: false,
  // Optional extra characteristics panel
  extraStatsEnabled: false,
  extraStatsSelected: new Set(),   // which ids are checked
  extraStatsRolls: {},             // last roll results { PSI: {total,dice,...}, ... }
  // Mobile tab: 'sheet' | 'stage' | 'log'
  mobileTab: 'stage',
  // Light/dark theme toggle
  themeLight: localStorage.getItem('theme') === 'light',
  // Heroic stat generation toggle (4×2D + 2×3D6 drop lowest)
  heroicRoll: false,
  // College skill pick: awaiting specialty selection for this skill name
  pcSkillSpecialtyPick: null,
  // Advancement bonus skill roll pending (after successful advancement)
  pendingAdvancementSkill: false,
  lastAdvanceRoll: null,     // stored advance roll data for restoring after bonus skill roll
  // Career skill specialty pick: set when a bare cascade skill (e.g. "Electronics") is rolled
  pendingCareerSpecialty: null,   // { skillName, level, tableKey, rollData, result } or null
  // Background skill phase: which cascade skill chip is expanded to show specialties
  bgExpandedCascade: null,
  // Shared cascade-skill specialty intercept (used by event/pre-career direct-API paths)
  pendingSkillGrant: null,
  // Done phase
  lastCapsule: null,         // cached narrative text from /api/character/capsule
  psionicsOpen: false,       // player has clicked "OPEN PSIONICS PANEL"
  // GM panel
  gmLastRolls: [],           // last set of forced rolls, shown in GM panel
};

// ------------------------------------------------------------
// Persistence
// ------------------------------------------------------------

function saveCharacter() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(character));
}

function loadCharacter() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) {
    try {
      character = JSON.parse(raw);
      // Restore species traits for saves that predate the traits field
      // (or that lost them due to a serialisation round-trip edge case).
      if ((!character.traits || !character.traits.length) && character.species_id) {
        const sp = SPECIES.find(s => s.id === character.species_id);
        if (sp && sp.traits && sp.traits.length) {
          character.traits = sp.traits;
          saveCharacter();  // persist the fix immediately
        }
      }
      return true;
    } catch (e) {
      console.warn('Corrupt saved character, starting fresh');
    }
  }
  return false;
}

async function freshCharacter() {
  const res = await fetch('/api/character/new', { method: 'POST' });
  const data = await res.json();
  character = data.character;
  uiState = { selectedSpecies: null, selectedBgSkills: new Set(), selectedPreCareerSkills: new Set(),
              selectedCareer: null, selectedAssignment: null, selectedCoverCareer: null, lastRoll: null,
              swapPick: null, swapA: 'EDU', swapB: 'STR',
              subPhase: null, pendingAge: false,
              agingResult: null, agingNextAction: null, agingSelectedStats: [],
              anagathicsPhaseDone: false, pendingNextTermAction: null,
              gmMode: uiState.gmMode,
              connectionsDone: false, connections: [],
              basicTrainingSkills: null,
              skillPackageApplied: false,
              pendingCareerSpecialty: null,
              bgExpandedCascade: null,
              pendingSkillGrant: null,
              lastCapsule: null, psionicsOpen: false, gmLastRolls: [] };
  saveCharacter();
}

// ------------------------------------------------------------
// API helpers
// ------------------------------------------------------------

async function apiCall(endpoint, extraData = {}) {
  // GM Mode: always prompt for roll overrides when panel input is empty.
  let gm_rolls = [];
  if (uiState.gmMode) {
    const input = document.getElementById('gm-roll-input');
    let raw = input ? input.value.trim() : '';
    if (!raw) {
      // Auto-prompt so every action can be overridden.
      const answer = window.prompt(
        '⚙ GM MODE — Enter roll total(s) for this action\n' +
        '(comma-separated for multiple rolls, or leave blank for random):',
        ''
      );
      raw = (answer || '').trim();
    }
    if (raw) {
      gm_rolls = raw.split(/[\s,]+/)
        .map(v => parseInt(v, 10))
        .filter(n => !isNaN(n));
      uiState.gmLastRolls = [...gm_rolls];
      if (input) input.value = '';
      renderGMPanel();
    }
  }

  const payload = { character, ...extraData, ...(gm_rolls.length ? { gm_rolls } : {}) };
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    let detail;
    try {
      const errJson = JSON.parse(body);
      detail = typeof errJson.detail === 'string'
        ? errJson.detail
        : JSON.stringify(errJson.detail);
    } catch {
      detail = body.trim().slice(0, 300) || `HTTP ${res.status}`;
    }
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function applyResponse(response) {
  if (response.character) {
    const incoming = response.character;
    // Guard: traits can go missing when an old save (pre-traits field) is
    // round-tripped through the API — the JSON omits the key, Pydantic uses
    // the default [], and it propagates.  If the incoming character has no
    // traits but we can look them up from the bootstrap SPECIES data, restore
    // them now.  This never fires when apply_species deliberately sets new
    // traits (those responses always carry non-empty traits).
    if (!incoming.traits || !incoming.traits.length) {
      const spId = incoming.species_id || (character && character.species_id);
      if (spId) {
        const sp = SPECIES.find(s => s.id === spId);
        if (sp && sp.traits && sp.traits.length) {
          incoming.traits = sp.traits;
        } else if (character && character.traits && character.traits.length) {
          // Fall back: keep whatever traits the current character already has.
          incoming.traits = character.traits;
        }
      }
    }
    character = incoming;
    saveCharacter();
  }
  // On mobile, switch to ACTION tab after any API response so the result is visible
  if (uiState.mobileTab !== 'stage') {
    uiState.mobileTab = 'stage';
  }
  return response;
}

// ------------------------------------------------------------
// DM calculator (mirror of dice.characteristic_dm)
// ------------------------------------------------------------

function charDM(score) {
  if (score == null || isNaN(score) || score <= 0) return -3;
  if (score <= 2) return -2;
  if (score <= 5) return -1;
  if (score <= 8) return 0;
  if (score <= 11) return 1;
  if (score <= 14) return 2;
  return 3;
}

function formatDM(dm) {
  if (dm > 0) return `+${dm}`;
  return `${dm}`;
}

// ------------------------------------------------------------
// Roll readout — shared across every phase so the dice are always visible
// ------------------------------------------------------------

// Cumulative percentile of the raw dice sum for n d6 — i.e. "this roll
// was better than or equal to X% of all possible rolls on this many d6."
// Probability-weighted so a 10 on 2d6 scores 92% (it really is lucky),
// not the naive 83% you'd get by dividing 10 by 12.
function diceLuckPercent(dice) {
  if (!Array.isArray(dice) || !dice.length) return null;
  const n = dice.length;
  const sum = dice.reduce((a, b) => a + b, 0);
  // Coefficients of (x + x^2 + ... + x^6)^n — dist[k] = # ways to roll total k.
  let dist = [0, 1, 1, 1, 1, 1, 1]; // 1d6
  for (let i = 1; i < n; i++) {
    const next = new Array(6 * (i + 1) + 1).fill(0);
    for (let j = 0; j < dist.length; j++) {
      if (!dist[j]) continue;
      for (let d = 1; d <= 6; d++) next[j + d] += dist[j];
    }
    dist = next;
  }
  const outcomes = Math.pow(6, n);
  let cumulative = 0;
  for (let j = 0; j <= sum && j < dist.length; j++) cumulative += dist[j] || 0;
  return Math.round((cumulative / outcomes) * 100);
}

function luckClass(pct) {
  if (pct === null || pct === undefined) return '';
  if (pct >= 85) return 'great';
  if (pct >= 60) return 'good';
  if (pct >= 30) return 'meh';
  return 'bad';
}

// Anagathics status info box (shown on advance/decide/mishap screens for awareness).
// Actual access roll happens at the START of the next term via anagathics_prompt.
function anagathicsBoxHTML() {
  if (character.total_terms + 1 < 4) return '';  // aging doesn't start until term 4+
  const active = character.anagathics_active;
  const terms = character.anagathics_terms_used ?? 0;
  if (active) {
    return `
      <div class="anagathics-box" style="margin-top:14px">
        <div class="anagathics-header">
          <strong>Anagathics active</strong>
          <span class="empty">+${terms} DM on aging · Double survival required</span>
        </div>
        <div class="anagathics-status">
          Terms on treatment: <strong>${terms}</strong>
          · Cost next term: 1D × Cr25,000 (at end of term)
        </div>
      </div>`;
  }
  return `
    <div class="anagathics-box" style="margin-top:14px">
      <div class="anagathics-header">
        <strong>Anagathics available</strong>
        <span class="empty">Roll SOC 10+ at the start of next term to access</span>
      </div>
      <div class="anagathics-status" style="color:var(--text-dim)">
        Not currently active · Aging roll will apply this term
      </div>
    </div>`;
}

function rollReadoutHTML(r, opts = {}) {
  // r is the .to_dict() output from engine.dice.RollResult
  //   dice: [1..6, 1..6], raw_total, modifier, total, target?, succeeded?
  const { label = null, outcome = null, showTarget = true } = opts;
  if (!r) return '';
  const dicePart = Array.isArray(r.dice) && r.dice.length
    ? `<span class="dice">[${r.dice.join(' · ')}]</span>`
    : '';
  const luckPct = diceLuckPercent(r.dice);
  const luckPart = luckPct !== null
    ? `<span class="roll-luck ${luckClass(luckPct)}" title="You rolled at or above ${luckPct}% of all possible ${r.dice.length}d6 outcomes.">${luckPct}%</span>`
    : '';
  const modPart = (r.modifier && r.modifier !== 0)
    ? `<span class="eq">${r.modifier > 0 ? '+' : ''}${r.modifier} DM</span>`
    : '';
  const totalPart = `<span class="total">${r.total}</span>`;
  const targetPart = (showTarget && r.target !== null && r.target !== undefined)
    ? `<span class="eq">vs ${r.target}+</span>`
    : '';
  let outcomeClass = outcome;
  if (outcomeClass === null && r.succeeded !== null && r.succeeded !== undefined) {
    outcomeClass = r.succeeded ? 'pass' : 'fail';
  }
  const outcomePart = outcomeClass === 'pass' ? '<span class="outcome pass">PASS</span>'
                    : outcomeClass === 'fail' ? '<span class="outcome fail">FAIL</span>'
                    : '';
  const labelPart = label ? `<span class="roll-label">${label}</span>` : '';
  return `
    <div class="roll-readout">
      ${labelPart}
      ${dicePart}
      ${luckPart}
      ${modPart}
      <span class="eq">=</span>
      ${totalPart}
      ${targetPart}
      ${outcomePart}
    </div>
  `;
}

// ------------------------------------------------------------
// Rendering: Character Sheet (left panel)
// ------------------------------------------------------------

const NOBLE_TITLES = { 11: 'Knight', 12: 'Baron', 13: 'Marquis', 14: 'Count', 15: 'Duke' };
// Noble titles apply to Third Imperium citizens (check society_id first,
// fall back to legacy species-id list for old saved characters).
const IMPERIAL_SPECIES = new Set(['imperial_human', 'imperial_aslan', 'imperial_vargr',
  'imperial_bwap', 'jonkeereen', 'luriani', 'human', 'solomani', 'vilani', 'mixed_human']);

function nobleTitle(speciesId, soc) {
  const isImperial = (character.society_id === 'third_imperium' || !character.society_id)
                  || IMPERIAL_SPECIES.has(speciesId);
  if (!isImperial) return null;
  return NOBLE_TITLES[soc] || (soc > 15 ? 'Archduke' : null);
}

function renderSheet() {
  const sheet = document.getElementById('sheet');
  const stats = character.characteristics;
  const _speciesChosen = !['characteristics', 'society'].includes(character.phase || '');
  const species = _speciesChosen
    ? (SPECIES.find((s) => s.id === character.species_id) || { name: '—' })
    : { name: 'Unknown' };

  const statCells = ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC']
    .map((stat) => {
      const val = stats[stat];
      const dm = charDM(val);
      return `
        <div class="stat-cell">
          <span class="stat-label">${stat}</span>
          <span class="stat-value">${val}</span>
          <span class="stat-dm">DM ${formatDM(dm)}</span>
        </div>
      `;
    }).join('')
    + (character.psi > 0 ? `
        <div class="stat-cell stat-cell-psi">
          <span class="stat-label">PSI</span>
          <span class="stat-value">${character.psi}</span>
          <span class="stat-dm">DM ${formatDM(charDM(character.psi))}</span>
        </div>
      ` : '');

  const skillsList = character.skills.length
    ? character.skills.map((s) => {
        const label = s.speciality ? `${s.name} (${s.speciality})` : s.name;
        return `<li><span>${label}</span><span class="skill-level">${s.level}</span></li>`;
      }).join('')
    : '<li class="empty">No skills yet</li>';

  const equipList = character.equipment.length
    ? character.equipment.map((e) => `<li>${e.name}${e.notes ? ` <span class="empty">— ${e.notes}</span>` : ''}</li>`).join('')
    : '<li class="empty">No equipment</li>';

  const traits = (character.traits || []);
  const traitsHTML = traits.length
    ? `<ul class="traits-list">${traits.map(t => `<li><strong>${t.name}:</strong> ${t.description}</li>`).join('')}</ul>`
    : '<p class="empty">No species traits</p>';

  const careersHTML = character.completed_careers.length
    ? `<ul class="skill-list">${character.completed_careers.map(c => {
        const careerDef = CAREERS.find(x => x.id === c.career_id);
        const asgnName = careerDef?.assignments?.[c.assignment_id]?.name || c.assignment_id;
        const rankStr = c.final_rank_title || (c.final_rank > 0 ? `Rank ${c.final_rank}` : 'No rank');
        return `<li><span>${careerDef?.name || c.career_id} — ${asgnName}</span><span class="skill-level">${c.terms_served}t</span></li><li style="border:none;padding:0 0 4px 8px;color:var(--muted);font-size:10px">${rankStr}, ${c.left_due_to}</li>`;
      }).join('')}</ul>`
    : '<p class="empty">No careers yet</p>';

  const associates = character.associates || [];
  const buckets = { contact: [], ally: [], rival: [], enemy: [] };
  associates.forEach((a, i) => {
    if (buckets[a.kind]) buckets[a.kind].push({ a, i });
  });
  const bucketOrder = [
    ['contact', 'Contacts'],
    ['ally', 'Allies'],
    ['rival', 'Rivals'],
    ['enemy', 'Enemies'],
  ];
  const associatesHTML = associates.length
    ? bucketOrder.map(([k, title]) => {
        const items = buckets[k];
        if (!items.length) return '';
        return `
          <div class="assoc-bucket assoc-kind-${k}">
            <div class="assoc-bucket-title">${title} <span class="assoc-count">${items.length}</span></div>
            <ul class="skill-list">
              ${items.map(({ a }) => `<li><span>${escapeHTML(a.description || '(unnamed)')}</span></li>`).join('')}
            </ul>
          </div>
        `;
      }).join('')
    : '<p class="empty">No associates yet</p>';

  sheet.innerHTML = `
    <div class="panel-header"><span class="led"></span><span>CHARACTER FILE</span></div>
    <div class="sheet-scroll">
      <div class="sheet-header">
        <div class="sheet-name-wrap">
          <input type="text" class="sheet-name-input" id="char-name" placeholder="[ Unnamed Traveller ]" value="${escapeAttr(character.name)}" />
          <button class="btn-gen-name" id="btn-gen-name" title="Generate species-appropriate name">↺</button>
        </div>
        <span class="sheet-homeworld-wrap">
          <input type="text" class="sheet-homeworld" id="char-homeworld" placeholder="Homeworld" value="${escapeAttr(character.homeworld)}" />
          <a href="https://travellermap.com/" target="_blank" rel="noopener noreferrer" class="homeworld-map-link" title="Open Traveller Map"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></a>
        </span>
        <input type="text" class="sheet-uwp" id="char-uwp" placeholder="UWP — e.g. A788899-C" value="${escapeAttr(character.homeworld_uwp)}" title="Universal World Profile" />
        <div class="sheet-meta">
          <span>SPECIES<br><strong>${species.name}</strong></span>
          <span>AGE<br><strong>${character.age}</strong></span>
          <span>TERMS<br><strong>${character.total_terms}</strong></span>
          <span>CREDITS<br><strong>Cr${character.credits.toLocaleString()}</strong></span>
          ${(() => { const t = nobleTitle(character.species_id, character.characteristics?.SOC); return t ? `<span class="noble-title-badge" title="Imperial Noble Title">TITLE<br><strong>${t}</strong></span>` : ''; })()}
        </div>
      </div>

      <div class="sheet-section">
        <h3>Characteristics</h3>
        <div class="stat-grid">${statCells}</div>
      </div>

      ${Object.keys(character.extra_characteristics || {}).length ? `
      <div class="sheet-section">
        <h3>Optional Characteristics</h3>
        <div class="stat-grid">${
          EXTRA_STATS.filter(s => character.extra_characteristics[s.id] != null).map(s => {
            const val = character.extra_characteristics[s.id];
            const dm = charDM(val);
            return `<div class="stat-cell stat-cell-extra">
              <span class="stat-label">${s.id}</span>
              <span class="stat-value">${val}</span>
              <span class="stat-dm extra-stat-name-tiny">${s.label}</span>
            </div>`;
          }).join('')
        }</div>
      </div>
      ` : ''}

      <div class="sheet-section">
        <h3>Skills</h3>
        <ul class="skill-list">${skillsList}</ul>
      </div>

      <div class="sheet-section">
        <h3>Careers</h3>
        ${careersHTML}
      </div>

      <div class="sheet-section">
        <h3>Associates</h3>
        ${associatesHTML}
      </div>

      <div class="sheet-section">
        <h3>Equipment</h3>
        <ul class="equipment-list">${equipList}</ul>
      </div>

      ${character.ship_shares > 0 ? `
      <div class="sheet-section">
        <h3>Ship Shares</h3>
        <div class="credits-line">${character.ship_shares} × MCr1</div>
      </div>` : ''}

      ${character.pension_per_year > 0 ? `
      <div class="sheet-section">
        <h3>Retirement Pension</h3>
        <div class="credits-line">Cr${character.pension_per_year.toLocaleString()}/year</div>
        <p class="empty">Based on ${character.total_terms} terms served.</p>
      </div>` : ''}

      ${(character.dm_next_qualification || character.dm_next_advancement || character.dm_next_benefit) ? `
      <div class="sheet-section">
        <h3>Pending DMs</h3>
        <ul class="skill-list">
          ${character.dm_next_qualification ? `<li><span>Next qualification</span><span class="skill-level">${formatDM(character.dm_next_qualification)}</span></li>` : ''}
          ${character.dm_next_advancement ? `<li><span>Next advancement</span><span class="skill-level">${formatDM(character.dm_next_advancement)}</span></li>` : ''}
          ${character.dm_next_benefit ? `<li><span>Next benefit</span><span class="skill-level">${formatDM(character.dm_next_benefit)}</span></li>` : ''}
        </ul>
      </div>` : ''}

      <div class="sheet-section">
        <h3>Species Traits</h3>
        ${traitsHTML}
      </div>

      ${character.medical_debt > 0 ? `
      <div class="sheet-section warn">
        <h3>Medical Debt</h3>
        <div class="credits-line danger">Cr${character.medical_debt.toLocaleString()} owed</div>
        <p class="empty">Deducted automatically from mustering-out cash rolls.</p>
      </div>` : ''}

      ${character.anagathics_active ? `
      <div class="sheet-section">
        <h3>Anagathics</h3>
        <ul class="skill-list">
          <li><span>Status</span><span class="skill-level" style="color:var(--success,#7fd87f)">ACTIVE</span></li>
          <li><span>Terms on treatment</span><span class="skill-level">${character.anagathics_terms_used ?? 0}</span></li>
          <li><span>Aging DM bonus</span><span class="skill-level">+${character.anagathics_terms_used ?? 0}</span></li>
        </ul>
      </div>` : ''}

      ${character.home_forces_enrolled ? `
      <div class="sheet-section">
        <h3>Home Forces Reserves</h3>
        <ul class="skill-list">
          <li><span>Component</span><span class="skill-level">${(character.home_forces_component || 'groundside').replace('_',' ')}</span></li>
          <li><span>Reserve Rank</span><span class="skill-level">${character.home_forces_rank}</span></li>
        </ul>
        <p class="empty">Nat-2 survival → extra Reserve Mishap roll.</p>
      </div>` : ''}

      ${character.solsec_monitor ? `
      <div class="sheet-section">
        <h3>SolSec Monitor</h3>
        <ul class="skill-list">
          <li><span>Monitor Rank</span><span class="skill-level">${character.solsec_monitor_rank}</span></li>
        </ul>
        <p class="empty">DM+1 advancement · nat-2 → SolSec Mishap · nat-12 → SolSec Event${character.solsec_monitor_rank >= 3 ? ' · +1 Benefit roll' : ''}.</p>
      </div>` : ''}

      <div class="sheet-section">
        <h3>Notes</h3>
        <textarea id="char-notes" class="sheet-notes" placeholder="Personality, quirks, contacts, anything you want on the sheet…" rows="5">${escapeHTML(character.user_notes || '')}</textarea>
      </div>
    </div>
  `;

  // Wire up name + homeworld
  document.getElementById('char-name').addEventListener('change', (e) => {
    character.name = e.target.value;
    saveCharacter();
  });
  document.getElementById('btn-gen-name').addEventListener('click', () => {
    const name = generateSpeciesName(character.species_id || 'imperial_human');
    character.name = name;
    document.getElementById('char-name').value = name;
    saveCharacter();
  });
  document.getElementById('char-homeworld').addEventListener('change', (e) => {
    character.homeworld = e.target.value;
    saveCharacter();
  });
  const uwpEl = document.getElementById('char-uwp');
  if (uwpEl) uwpEl.addEventListener('change', (e) => {
    const stripped = e.target.value.replace(/\s+/g, '');
    character.homeworld_uwp = stripped;
    e.target.value = stripped;
    saveCharacter();
  });
  const notesEl = document.getElementById('char-notes');
  if (notesEl) notesEl.addEventListener('input', (e) => {
    character.user_notes = e.target.value;
    // Debounce the save so every keystroke doesn't hit localStorage
    clearTimeout(window._notesSaveTimer);
    window._notesSaveTimer = setTimeout(saveCharacter, 400);
  });
}

// ------------------------------------------------------------
// Rendering: Log (right panel)
// ------------------------------------------------------------

function renderLog() {
  const log = document.getElementById('log');

  // Build origin header — species, society, homeworld
  const _speciesChosen2 = !['characteristics', 'society'].includes(character.phase || '');
  const _sp = _speciesChosen2 ? (SPECIES.find(s => s.id === character.species_id) || null) : null;
  const _spName = _sp ? _sp.name : (_speciesChosen2 && character.species_id ? character.species_id : null);
  const _soc = (SOCIETIES || []).find(s => s.id === character.society_id);
  const _socName = _soc ? _soc.name : character.society_id || null;
  const _hw = character.homeworld ? character.homeworld + (character.homeworld_uwp ? ` (${character.homeworld_uwp})` : '') : null;

  const originItems = [];
  if (_spName)  originItems.push(`<li class="log-origin">Species · <strong>${escapeHTML(_spName)}</strong></li>`);
  if (_socName) originItems.push(`<li class="log-origin">Society · <strong>${escapeHTML(_socName)}</strong></li>`);
  if (_hw)      originItems.push(`<li class="log-origin">Origin  · <strong>${escapeHTML(_hw)}</strong></li>`);
  if (originItems.length) originItems.push(`<li class="log-origin log-origin-divider"></li>`);

  const notes = (character.notes || []).slice(-80).map(n => `<li>${escapeHTML(n)}</li>`).join('');
  log.innerHTML = originItems.join('') + notes;
  log.scrollTop = log.scrollHeight;
}

function escapeHTML(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/** Escape for use inside a quoted HTML attribute (e.g. value="..."). */
function escapeAttr(s) {
  return escapeHTML(String(s || '')).replace(/"/g, '&quot;');
}

/**
 * Render the treatment-choice screen (accept stat loss OR pay debt).
 * Used in pre-career and career/mishap injury flows.
 * btnPrefix distinguishes the button IDs so multiple phases can coexist.
 */
function renderInjuryTreatmentChoiceHTML(tc, btnPrefix) {
  const gross = tc.gross_debt || 0;
  const net = tc.net_debt || 0;
  const covered = tc.covered || 0;
  const pct = tc.coverage_pct || 0;
  const stat = tc.chosen_stat;
  const primaryLoss = tc.primary_loss || 0;
  const secs = tc.secondary_losses || [];
  const autoAmt = tc.auto_reduce_others || 0;

  const lossLines = [`${stat}: ${tc.primary_old} → ${tc.primary_new} (−${primaryLoss})`];
  secs.forEach(s => lossLines.push(`${s.stat}: ${s.old} → ${s.new} (−${s.loss})`));

  const freeCover = gross > 0 && net === 0;

  return `
    <div class="event-box" style="margin-top:14px;border-color:var(--amber)">
      <span class="event-label" style="color:var(--amber)">TREATMENT CHOICE — ${escapeHTML(tc.title || 'Injury')}</span>
      <p style="margin:8px 0 4px">You took a hit. Choose one option:</p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px">
        <div style="border:1px solid var(--border);border-radius:4px;padding:10px">
          <strong>Accept Injury</strong>
          <p style="font-size:12px;color:var(--text-dim);margin:4px 0">No cost. Permanent stat reduction:</p>
          ${lossLines.map(l => `<div class="dm-chip" style="margin:2px 0">${escapeHTML(l)}</div>`).join('')}
          <button class="btn ghost" style="width:100%;margin-top:8px" id="${btnPrefix}-take">TAKE THE INJURY</button>
        </div>
        <div style="border:1px solid var(--border);border-radius:4px;padding:10px">
          <strong>Pay for Treatment</strong>
          <p style="font-size:12px;color:var(--text-dim);margin:4px 0">Stats stay intact.</p>
          ${gross > 0 ? `
            <div class="dm-chip" style="margin:2px 0">Gross: Cr${gross.toLocaleString()}</div>
            <div class="dm-chip applied" style="margin:2px 0">Career covers ${pct}%: −Cr${covered.toLocaleString()}</div>
            <div class="dm-chip ${net > 0 ? 'danger' : 'applied'}" style="margin:2px 0;${net > 0 ? 'border-color:var(--danger)' : ''}">
              You owe: Cr${net.toLocaleString()}${freeCover ? ' (FREE — fully covered!)' : ''}
            </div>` : '<div class="dm-chip applied">No cost</div>'}
          <button class="btn primary" style="width:100%;margin-top:8px" id="${btnPrefix}-pay">
            ${freeCover ? 'ACCEPT TREATMENT (FREE) →' : `PAY Cr${net.toLocaleString()} →`}
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Wire injury treatment choice buttons. After clicking, calls /api/character/injury-payment
 * and invokes onDone(response) to let the caller continue the phase.
 */
async function wireInjuryTreatmentButtons(btnPrefix, onDone) {
  const takeBtn = document.getElementById(`${btnPrefix}-take`);
  const payBtn  = document.getElementById(`${btnPrefix}-pay`);
  if (takeBtn) takeBtn.addEventListener('click', async () => {
    try {
      const resp = await apiCall('/api/character/injury-payment', { pay: false });
      await applyResponse(resp);
      onDone(resp, false);
    } catch (e) { alert(e.message); }
  });
  if (payBtn) payBtn.addEventListener('click', async () => {
    try {
      const resp = await apiCall('/api/character/injury-payment', { pay: true });
      await applyResponse(resp);
      onDone(resp, true);
    } catch (e) { alert(e.message); }
  });
}

/**
 * Build a human-readable medical bills alert string from an injury-choice response.
 * Returns an empty string if no debt was incurred.
 */
function formatMedicalBillsMsg(response) {
  const gross = response.gross_debt || 0;
  if (gross <= 0) return '';
  const applied = response.applied || [];
  const bills = response.medical_bills_roll;
  const net = response.medical_debt_added || 0;
  const total = response.medical_debt_total || 0;

  let msg = `Injury applied: ${applied.join(', ') || 'resolved'}.`;
  msg += `\n\nMedical Bills (MgT2e p.47):`;
  msg += `\n  Gross debt: Cr${gross.toLocaleString()} (Cr5,000 × ${gross / 5000} pts)`;

  if (bills) {
    const rollStr = `2D(${bills.roll?.total ?? '?'}) + Rank ${bills.rank_dm} = ${bills.total}`;
    msg += `\n  Career category: ${bills.category}`;
    msg += `\n  Medical roll: ${rollStr}`;
    msg += `\n  Coverage: ${bills.coverage_pct}% — Cr${bills.covered.toLocaleString()} paid by career`;
    msg += `\n  You owe: Cr${net.toLocaleString()}`;
  } else {
    msg += `\n  You owe: Cr${net.toLocaleString()}`;
  }

  if (total > 0) {
    msg += `\n  Total medical debt: Cr${total.toLocaleString()} (deducted from mustering-out cash)`;
  }
  return msg;
}

// ------------------------------------------------------------
// Rendering: Stage (center panel — phase-specific UI)
// ------------------------------------------------------------

// ============================================================
// Shared cascade-skill specialty intercept
// Works across any phase: pre-career event10, any-skill, event skills,
// contested skills. Stores a callback; renderStage injects the overlay.
// ============================================================

let _skillGrantCallback = null;  // async (fullSkillText: string) => void

/**
 * Call before any direct-API skill grant.
 * If skillText is a bare cascade skill, stores the callback, sets
 * uiState.pendingSkillGrant, and returns true (caller must return/abort).
 * Otherwise returns false (caller proceeds normally).
 *
 * @param {string} skillText  e.g. "Electronics" or "Electronics (Computers) 1"
 * @param {function} callback async function called with the full skill text after specialty chosen
 */
function interceptCascadeSkill(skillText, callback) {
  const text = (skillText || '').trim();
  // Strip trailing level number to get bare skill name
  const bare = text.replace(/\s+\d+\s*$/, '').trim();
  // If it already has a specialty (parenthetical), no intercept needed
  if (/\(/.test(bare)) return false;
  if (!CASCADE_SKILLS[bare]) return false;
  // Parse level from original text
  const levelMatch = text.match(/\s+(\d+)\s*$/);
  const level = levelMatch ? parseInt(levelMatch[1], 10) : 1;
  uiState.pendingSkillGrant = { skillName: bare, level };
  _skillGrantCallback = callback;
  renderStage();
  return true;
}

function renderStage() {
  const stage = document.getElementById('stage');

  // Cascade specialty picker overlay — injected on top of whatever phase is active
  if (uiState.pendingSkillGrant) {
    const { skillName, level } = uiState.pendingSkillGrant;
    const specs = CASCADE_SKILLS[skillName] || [];
    stage.innerHTML = `
      <div class="panel-header"><span class="led"></span><span>CHOOSE SPECIALTY</span></div>
      <div class="stage-content">
        <div class="phase-label">Cascade Skill — ${escapeHTML(skillName)}</div>
        <h2 class="phase-title">${escapeHTML(skillName)} requires a specialty</h2>
        <p class="phase-body">Pick one specialty to gain at level ${level}${level === 0 ? ' (background skill)' : ''}:</p>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px">
          ${specs.map(s => `<button class="btn ghost specialty-chip" data-grant-specialty="${escapeHTML(s)}">${escapeHTML(s)}</button>`).join('')}
        </div>
        <div class="phase-actions" style="margin-top:16px">
          <button class="btn ghost" id="btn-cancel-specialty">CANCEL</button>
        </div>
      </div>
    `;
    // Wire specialty chips
    stage.querySelectorAll('[data-grant-specialty]').forEach(chip => {
      chip.addEventListener('click', async () => {
        const spec = chip.dataset.grantSpecialty;
        const fullText = `${skillName} (${spec}) ${level}`;
        const cb = _skillGrantCallback;
        uiState.pendingSkillGrant = null;
        _skillGrantCallback = null;
        if (cb) await cb(fullText);
      });
    });
    const btnCancel = stage.querySelector('#btn-cancel-specialty');
    if (btnCancel) btnCancel.addEventListener('click', () => {
      uiState.pendingSkillGrant = null;
      _skillGrantCallback = null;
      renderStage();
    });
    return;
  }

  if (character.dead) {
    stage.innerHTML = renderDeadStage();
    wireDeadStage();
    return;
  }

  switch (character.phase) {
    case 'characteristics':
      stage.innerHTML = renderCharacteristicsPhase();
      wireCharacteristicsPhase();
      break;
    case 'society':
      stage.innerHTML = renderSocietyPhase();
      wireSocietyPhase();
      break;
    case 'species':
      stage.innerHTML = renderSpeciesPhase();
      wireSpeciesPhase();
      break;
    case 'background':
      stage.innerHTML = renderBackgroundPhase();
      wireBackgroundPhase();
      break;
    case 'pre_career':
      stage.innerHTML = renderPreCareerPhase();
      wirePreCareerPhase();
      break;
    case 'career':
      stage.innerHTML = renderCareerPhase();
      wireCareerPhase();
      break;
    case 'mustering':
      stage.innerHTML = renderMusterPhase();
      wireMusterPhase();
      break;
    case 'skill_package':
      stage.innerHTML = renderSkillPackagePhase();
      wireSkillPackagePhase();
      break;
    case 'done':
      stage.innerHTML = renderDonePhase();
      wireDonePhase();
      break;
    default:
      stage.innerHTML = `<div class="stage-content"><p>Unknown phase: ${character.phase}</p></div>`;
  }
}

// ============================================================
// PHASE 1: Characteristics
// ============================================================

function rollQuality(total) {
  // Expected range for 6 * 2D: mean 42, SD ~5.9. Thresholds picked to give
  // descriptive names the player can parse at a glance.
  if (total >= 60) return { tier: 'Exceptional', note: 'elite rolls — very few Travellers have this starting material', cls: 'q-elite' };
  if (total >= 54) return { tier: 'Strong',      note: 'well above average — most careers will take you', cls: 'q-strong' };
  if (total >= 48) return { tier: 'Solid',       note: 'above average — a capable Traveller', cls: 'q-solid' };
  if (total >= 36) return { tier: 'Average',     note: 'typical 2D spread — expect some hard survival rolls', cls: 'q-average' };
  if (total >= 30) return { tier: 'Lean',        note: 'below average — consider a reroll or a rearrange', cls: 'q-lean' };
  return                    { tier: 'Rough',      note: 'brutal rolls — strongly consider rerolling', cls: 'q-rough' };
}

function renderCharacteristicsPhase() {
  const hasRolled = Object.values(character.characteristics).some(v => v > 0);
  const STATS = ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC'];

  // Compute best / worst stat so they can be highlighted in the grid and called out.
  let bestStat = null, worstStat = null, total = 0, totalDM = 0;
  if (hasRolled) {
    for (const s of STATS) {
      const v = character.characteristics[s];
      total += v;
      totalDM += charDM(v);
      if (bestStat === null || v > character.characteristics[bestStat]) bestStat = s;
      if (worstStat === null || v < character.characteristics[worstStat]) worstStat = s;
    }
  }
  const q = hasRolled ? rollQuality(total) : null;

  // Stat grid — each cell shows rolled value + DM, makes swap decisions concrete.
  const statGrid = hasRolled ? `
    <div class="stat-grid-rolled">
      ${STATS.map(stat => {
        const val = character.characteristics[stat];
        const dm = charDM(val);
        const extra = [];
        if (stat === bestStat && bestStat !== worstStat) extra.push('best');
        if (stat === worstStat && bestStat !== worstStat) extra.push('worst');
        if (uiState.swapPick === stat) extra.push('picked');
        return `
          <div class="stat-cell-rolled ${extra.join(' ')}"
               data-stat="${stat}">
            <span class="stat-label">${stat}</span>
            <span class="stat-value">${val}</span>
            <span class="stat-dm">DM ${formatDM(dm)}</span>
            ${(uiState.gmMode || character.boon_rolls_remaining > 0) ? `
              <button class="boon-btn" data-boon-stat="${stat}" title="Re-roll ${stat}, keep the higher value">BOON</button>
            ` : ''}
          </div>
        `;
      }).join('')}
    </div>
  ` : '';

  // Roll quality readout — sits between the dice banner and the stat grid
  // so the player can tell at a glance whether this is a keep or a reroll.
  const qualityReadout = hasRolled ? `
    <div class="roll-quality ${q.cls}">
      <div class="rq-header">
        <span class="rq-label">ROLL QUALITY</span>
        <span class="rq-tier">${q.tier}</span>
      </div>
      <div class="rq-stats">
        <span class="rq-stat"><span class="rq-k">TOTAL</span><span class="rq-v">${total}</span><span class="rq-cmp">of 72 avg 42</span></span>
        <span class="rq-stat"><span class="rq-k">NET DM</span><span class="rq-v">${formatDM(totalDM)}</span></span>
        <span class="rq-stat"><span class="rq-k">BEST</span><span class="rq-v">${bestStat} ${character.characteristics[bestStat]}</span></span>
        <span class="rq-stat"><span class="rq-k">WORST</span><span class="rq-v">${worstStat} ${character.characteristics[worstStat]}</span></span>
      </div>
      <div class="rq-note">${q.note}</div>
    </div>
  ` : '';

  // Swap controls — two dropdowns + a button. Pre-select the current
  // pick if the user clicked a tile.
  const swapRow = hasRolled ? `
    <div class="swap-row">
      <span class="swap-label">REARRANGE</span>
      <select id="swap-a" class="swap-select">
        ${STATS.map(s => `<option value="${s}" ${s === (uiState.swapA || 'EDU') ? 'selected' : ''}>${s} (${character.characteristics[s]})</option>`).join('')}
      </select>
      <span class="swap-arrow">↔</span>
      <select id="swap-b" class="swap-select">
        ${STATS.map(s => `<option value="${s}" ${s === (uiState.swapB || 'STR') ? 'selected' : ''}>${s} (${character.characteristics[s]})</option>`).join('')}
      </select>
      <button class="btn" id="btn-swap-stats">SWAP</button>
    </div>
    <p class="swap-hint">Click a tile above to quick-pick, or use the dropdowns. Example: moving EDU→STR to build a brawler.</p>
  ` : '';

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 01 — CHARACTERISTICS</span></div>
    <div class="stage-content">
      <div class="phase-label">Terminal Session Begin</div>
      <h2 class="phase-title">Roll Your Traveller</h2>
      <p class="phase-subtitle">Six characteristics define the bright-eyed 18-year-old about to take on the universe.</p>

      <div class="phase-body">
        <p>You are about to generate a Traveller. Each characteristic — <strong>STR</strong>, <strong>DEX</strong>, <strong>END</strong>, <strong>INT</strong>, <strong>EDU</strong>, <strong>SOC</strong> — is determined by rolling 2D. The resulting score yields a Dice Modifier that will govern almost every roll your Traveller makes across their life.</p>
        <p><em>After rolling, you can rearrange values between characteristics. You can keep rerolling and swapping until you commit to a species — then the numbers are locked in.</em></p>
      </div>

      ${hasRolled ? `
        <div class="roll-readout">
          <span class="dice">2D × 6</span>
          <span class="eq">—</span>
          <span class="total">ROLLED</span>
        </div>
      ` : `
        <div class="roll-readout" style="opacity:0.4">
          <span class="dice">—</span>
          <span class="eq">awaiting</span>
          <span class="total">input</span>
        </div>
      `}

      ${qualityReadout}
      ${statGrid}
      ${swapRow}

      ${uiState.gmMode ? `
        <div class="gm-panel">
          <span class="gm-badge">GM MODE</span>
          <label class="gm-field">
            BOON POOL
            <input type="number" id="gm-boon-pool" min="0" max="20" value="${character.boon_rolls_total}" />
            <button class="btn ghost" id="btn-set-boon-pool">SET</button>
          </label>
          <span class="gm-hint">Click any stat value to edit directly. BOON re-rolls keep the higher value.</span>
        </div>
      ` : ''}
      ${(!uiState.gmMode && character.boon_rolls_remaining > 0) ? `
        <div class="boon-banner">
          <strong>${character.boon_rolls_remaining}</strong> boon roll${character.boon_rolls_remaining === 1 ? '' : 's'} available. Click BOON on any stat to re-roll it — you keep the higher.
        </div>
      ` : ''}

      <div class="phase-actions">
        <button class="btn primary" id="btn-roll-stats">${hasRolled ? 'REROLL ALL' : (uiState.heroicRoll ? 'ROLL HEROIC' : 'ROLL 2D × 6')}</button>
        <button class="btn ${uiState.heroicRoll ? 'btn-heroic-active' : ''}" id="btn-toggle-heroic">
          ⚔ ${uiState.heroicRoll ? 'HEROIC ON' : 'HEROIC'}
          <span class="heroic-mechanic">${uiState.heroicRoll ? '4 stats: 2D · 2 stats: 3D6 drop lowest' : '4×2D + 2 stats rolled 3D6, drop lowest die'}</span>
        </button>
        <button class="btn" id="btn-to-species" ${hasRolled ? '' : 'disabled'}>CHOOSE ORIGIN →</button>
      </div>

      <!-- Optional extra characteristics -->
      <div class="extra-stats-section">
        <button class="btn extra-stats-toggle ${uiState.extraStatsEnabled ? 'btn-heroic-active' : ''}" id="btn-toggle-extra-stats">
          ◉ OPTIONAL STATS
          <span class="heroic-mechanic">House-rule extras — PSI, Wealth, Luck, Morale, Sanity, Territory</span>
        </button>
        <!-- Grid is always in the DOM; JS shows/hides it directly so scroll position is preserved -->
        <div id="extra-stats-wrapper" style="display:${uiState.extraStatsEnabled ? 'block' : 'none'}">
          <div class="extra-stats-grid">
            ${EXTRA_STATS.map(s => {
              const rolled = (character.extra_characteristics || {})[s.id];
              const checked = uiState.extraStatsSelected.has(s.id);
              const rollResult = uiState.extraStatsRolls[s.id];
              return `
                <label class="extra-stat-row ${checked ? 'extra-stat-checked' : ''}">
                  <input type="checkbox" class="extra-stat-cb" data-stat="${s.id}" ${checked ? 'checked' : ''} />
                  <span class="extra-stat-abbr">${s.id}</span>
                  <span class="extra-stat-label">${s.label}</span>
                  <span class="extra-stat-desc">${s.desc}</span>
                  ${rolled != null ? `<span class="extra-stat-val">${rolled}${rollResult?.heroic ? '*' : ''}</span>` : '<span class="extra-stat-val extra-stat-unrolled">—</span>'}
                </label>`;
            }).join('')}
          </div>
          <div class="extra-stats-actions">
            <button class="btn primary" id="btn-roll-extra-stats"
              ${uiState.extraStatsSelected.size === 0 ? 'disabled' : ''}>
              ROLL SELECTED (${uiState.extraStatsSelected.size})
            </button>
            ${uiState.heroicRoll ? `<span class="extra-stat-desc" style="align-self:center">Heroic: 3D drop lowest</span>` : ''}
          </div>
        </div>
      </div>
    </div>
  `;
}

function wireCharacteristicsPhase() {
  document.getElementById('btn-toggle-heroic').addEventListener('click', () => {
    uiState.heroicRoll = !uiState.heroicRoll;
    renderAll();
  });
  document.getElementById('btn-roll-stats').addEventListener('click', async () => {
    uiState.swapPick = null;
    const response = await apiCall('/api/character/roll-characteristics', { heroic: uiState.heroicRoll });
    await applyResponse(response);
    renderAll();
  });
  document.getElementById('btn-to-species').addEventListener('click', () => {
    uiState.swapPick = null;
    character.phase = 'society';
    saveCharacter();
    renderAll();
  });

  // Extra stats toggle — direct DOM show/hide, no full re-render (avoids scroll reset)
  document.getElementById('btn-toggle-extra-stats')?.addEventListener('click', () => {
    uiState.extraStatsEnabled = !uiState.extraStatsEnabled;
    const btn = document.getElementById('btn-toggle-extra-stats');
    if (btn) btn.classList.toggle('btn-heroic-active', uiState.extraStatsEnabled);
    const wrapper = document.getElementById('extra-stats-wrapper');
    if (wrapper) {
      wrapper.style.display = uiState.extraStatsEnabled ? 'block' : 'none';
      if (uiState.extraStatsEnabled) {
        wrapper.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  });
  // Extra stat checkboxes
  document.querySelectorAll('.extra-stat-cb').forEach(cb => {
    cb.addEventListener('change', () => {
      if (cb.checked) uiState.extraStatsSelected.add(cb.dataset.stat);
      else uiState.extraStatsSelected.delete(cb.dataset.stat);
      renderAll();
    });
  });
  // Roll extra stats button
  document.getElementById('btn-roll-extra-stats')?.addEventListener('click', async () => {
    const chosen = Array.from(uiState.extraStatsSelected);
    if (!chosen.length) return;
    const response = await apiCall('/api/character/roll-extra-characteristics', {
      heroic: uiState.heroicRoll,
      extra_stats: chosen,
    });
    await applyResponse(response);
    // Store roll details for display
    if (response.rolls) uiState.extraStatsRolls = { ...uiState.extraStatsRolls, ...response.rolls };
    renderAll();
  });

  // Click-to-pick on stat tiles: first click sets slot A, second sets B
  // and auto-triggers a swap.
  document.querySelectorAll('.stat-cell-rolled').forEach(cell => {
    cell.addEventListener('click', async () => {
      const stat = cell.dataset.stat;
      if (!uiState.swapPick) {
        uiState.swapPick = stat;
        uiState.swapA = stat;
        renderAll();
        return;
      }
      if (uiState.swapPick === stat) {
        // Same tile clicked again — cancel pick.
        uiState.swapPick = null;
        renderAll();
        return;
      }
      // Second pick — perform the swap immediately.
      const a = uiState.swapPick;
      const b = stat;
      uiState.swapPick = null;
      uiState.swapA = a;
      uiState.swapB = b;
      try {
        const response = await apiCall('/api/character/swap-stats', { stat_a: a, stat_b: b });
        await applyResponse(response);
      } catch (e) {
        alert(e.message);
      }
      renderAll();
    });
  });

  // Dropdown swap
  const swapA = document.getElementById('swap-a');
  const swapB = document.getElementById('swap-b');
  const swapBtn = document.getElementById('btn-swap-stats');
  if (swapA) swapA.addEventListener('change', () => { uiState.swapA = swapA.value; });
  if (swapB) swapB.addEventListener('change', () => { uiState.swapB = swapB.value; });
  if (swapBtn) {
    swapBtn.addEventListener('click', async () => {
      const a = swapA.value;
      const b = swapB.value;
      if (a === b) {
        alert('Pick two different characteristics to swap.');
        return;
      }
      try {
        const response = await apiCall('/api/character/swap-stats', { stat_a: a, stat_b: b });
        await applyResponse(response);
      } catch (e) {
        alert(e.message);
      }
      renderAll();
    });
  }

  // Boon buttons per stat cell
  document.querySelectorAll('[data-boon-stat]').forEach(btn => {
    btn.addEventListener('click', async (ev) => {
      ev.stopPropagation();  // don't trigger the tile's swap-pick
      const stat = btn.dataset.boonStat;
      try {
        const response = await apiCall('/api/character/boon', { stat });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'boon',
          data: response.roll,
          stat: response.stat,
          old: response.old,
          new: response.new,
          kept: response.kept,
        };
      } catch (e) {
        alert(e.message);
      }
      renderAll();
    });
  });

  // GM: set boon pool
  const gmBoonPool = document.getElementById('btn-set-boon-pool');
  if (gmBoonPool) {
    gmBoonPool.addEventListener('click', async () => {
      const count = parseInt(document.getElementById('gm-boon-pool').value, 10) || 0;
      try {
        const response = await apiCall('/api/character/boon-pool', { count });
        await applyResponse(response);
      } catch (e) { alert(e.message); }
      renderAll();
    });
  }

  // GM: direct-edit a stat by double-clicking its value
  if (uiState.gmMode) {
    document.querySelectorAll('.stat-cell-rolled .stat-value').forEach(el => {
      el.addEventListener('dblclick', (ev) => {
        const cell = ev.target.closest('[data-stat]');
        const stat = cell?.dataset?.stat;
        if (!stat) return;
        const current = character.characteristics[stat];
        const nextStr = prompt(`Set ${stat} to:`, String(current));
        if (nextStr === null) return;
        const next = parseInt(nextStr, 10);
        if (isNaN(next) || next < 0 || next > 20) {
          alert('Enter a number between 0 and 20.');
          return;
        }
        character.characteristics[stat] = next;
        character.notes.push(`GM: set ${stat} to ${next} (was ${current}).`);
        saveCharacter();
        renderAll();
      });
    });
  }
}

// ============================================================
// PHASE 2a: Society of Origin
// ============================================================

function renderSocietyPhase() {
  const selected = character.society_id || '';
  const cards = SOCIETIES.map((soc, idx) => {
    const num = String(idx + 1).padStart(2, '0');
    const isSelected = selected === soc.id;
    const speciesCount = soc.species_ids.length;
    const speciesLabel = speciesCount === 1 ? '1 species' : `${speciesCount} species`;
    return `
      <button class="card ${isSelected ? 'selected' : ''}" data-society="${soc.id}">
        <div class="card-title">${num}. ${soc.name}</div>
        <div class="card-meta">${soc.subtitle} · ${speciesLabel}</div>
        <div class="card-desc">${soc.description}</div>
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02 — SOCIETY OF ORIGIN</span></div>
    <div class="stage-content">
      <div class="phase-label">Cultural Background</div>
      <h2 class="phase-title">Where Were You Raised?</h2>
      <p class="phase-subtitle">Your society of origin determines which species are available and shapes your cultural background. It does not restrict your career choices — Travellers move between polities.</p>

      <div class="card-grid">${cards}</div>

      <div class="phase-actions">
        <button class="btn ghost" id="btn-back-society">← BACK</button>
        <button class="btn primary" id="btn-confirm-society" ${selected ? '' : 'disabled'}>
          SELECT SPECIES →
        </button>
      </div>
    </div>
  `;
}

function wireSocietyPhase() {
  document.querySelectorAll('[data-society]').forEach(card => {
    card.addEventListener('click', () => {
      character.society_id = card.dataset.society;
      uiState.selectedSpecies = null; // reset any prior species pick when society changes
      saveCharacter();
      renderStage();
    });
  });

  document.getElementById('btn-back-society').addEventListener('click', () => {
    character.phase = 'characteristics';
    saveCharacter();
    renderAll();
  });

  const confirmBtn = document.getElementById('btn-confirm-society');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => {
      if (!character.society_id) return;
      character.phase = 'species';
      saveCharacter();
      renderAll();
    });
  }
}

// ============================================================
// PHASE 2b: Species
// ============================================================

function renderSpeciesPhase() {
  // If a Heritage Roll result is pending, show the result panel instead
  if (uiState.racialBackgroundResult) {
    return renderRacialBackgroundResult();
  }

  const selected = uiState.selectedSpecies || character.species_id;
  const speciesApplied = character.species_id && character.traits && character.traits.length >= 0 && character.phase !== 'species';

  // Filter species list by the selected society
  const activeSociety = SOCIETIES.find(s => s.id === (character.society_id || 'third_imperium'));
  const allowedIds = activeSociety ? new Set(activeSociety.species_ids) : null;
  const filteredSpecies = allowedIds ? SPECIES.filter(sp => allowedIds.has(sp.id)) : SPECIES;

  const cards = filteredSpecies.map(sp => {
    const isRollTrigger = !!sp.racial_background_roll;
    const modsText = isRollTrigger
      ? '2D Heritage Roll'
      : (Object.entries(sp.characteristic_modifiers)
          .filter(([, v]) => v !== 0)
          .map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`)
          .join(' · ') || 'No modifiers');
    return `
      <button class="card ${selected === sp.id ? 'selected' : ''}" data-species="${sp.id}">
        <div class="card-title">${sp.name}</div>
        <div class="card-meta">${modsText}</div>
        <div class="card-desc">${sp.description}</div>
        ${isRollTrigger ? '<div class="card-meta" style="color:var(--amber)">🎲 Roll determines your exact heritage</div>' : ''}
      </button>
    `;
  }).join('');

  const selectedSp = SPECIES.find(s => s.id === selected);
  const traitsPanel = selectedSp && selectedSp.traits.length ? `
    <div class="species-traits-panel">
      <h4>Species Traits — ${selectedSp.name}</h4>
      ${selectedSp.traits.map(t => `
        <div class="trait">
          <span class="trait-name">${t.name}</span>
          <span class="trait-desc">${t.description}</span>
        </div>
      `).join('')}
    </div>
  ` : (selectedSp ? '<p class="empty" style="margin-top:14px">No special traits. The baseline Traveller experience.</p>' : '');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02b — SPECIES SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Genetic Profile</div>
      <h2 class="phase-title">Choose Your Species</h2>
      <p class="phase-subtitle">Species modifiers apply immediately to your rolled characteristics.</p>

      <div class="species-intro">
        <p>
          ${activeSociety
            ? `Showing species available to characters raised in the <strong>${activeSociety.name}</strong>.`
            : 'Showing all available species.'
          }
          Species modifiers apply once, now, to the characteristics you just rolled.
        </p>
        <p class="species-intro-hint">
          <em>Single-click to preview traits · Double-click to apply immediately.</em>
        </p>
      </div>

      <div class="card-grid">${cards}</div>

      ${traitsPanel}

      <div class="phase-actions">
        <button class="btn ghost" id="btn-back-stats">← ORIGIN</button>
        <button class="btn primary" id="btn-apply-species" ${selected ? '' : 'disabled'}>
          ${selectedSp?.racial_background_roll
            ? '🎲 ROLL HERITAGE →'
            : 'APPLY ' + (selectedSp ? selectedSp.name.toUpperCase() : 'SPECIES') + ' →'}
        </button>
      </div>
    </div>
  `;
}

function renderRacialBackgroundResult() {
  const result = uiState.racialBackgroundResult;
  const resolvedSp = SPECIES.find(s => s.id === character.species_id);
  const dice = result.heritage_roll?.dice || [];
  const total = result.heritage_roll?.total ?? '?';
  const mods = resolvedSp ? Object.entries(resolvedSp.characteristic_modifiers || {})
    .filter(([, v]) => v !== 0)
    .map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`)
    .join(' · ') : '';

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02b — HERITAGE ROLL</span></div>
    <div class="stage-content">
      <div class="phase-label">Solomani Heritage Determination</div>
      <h2 class="phase-title">Heritage Determined</h2>
      <p class="phase-subtitle">A 2D roll determines your ancestry within the Solomani Confederation.</p>

      <div class="roll-result-block" style="text-align:center;margin:24px 0">
        <div style="font-size:11px;letter-spacing:2px;color:var(--text-dim);margin-bottom:8px">HERITAGE ROLL</div>
        <div style="font-size:48px;font-weight:900;color:var(--accent)">${total}</div>
        <div style="font-size:13px;color:var(--text-dim)">(${dice.join(' + ')})</div>
      </div>

      <div class="result-block" style="border:1px solid var(--accent);border-radius:6px;padding:16px;margin-bottom:20px">
        <div style="font-size:11px;letter-spacing:2px;color:var(--accent);margin-bottom:6px">RESULT</div>
        <div style="font-size:20px;font-weight:700">${result.result_name}</div>
        ${mods ? `<div style="font-size:12px;color:var(--text-dim);margin-top:4px">Characteristic modifiers: ${mods}</div>` : ''}
        ${resolvedSp?.description ? `<p style="font-size:13px;margin-top:10px">${resolvedSp.description}</p>` : ''}
      </div>

      ${resolvedSp?.traits?.length ? `
        <div class="species-traits-panel">
          <h4>Heritage Traits — ${resolvedSp.name}</h4>
          ${resolvedSp.traits.map(t => `
            <div class="trait">
              <span class="trait-name">${t.name}</span>
              <span class="trait-desc">${t.description}</span>
            </div>
          `).join('')}
        </div>
      ` : ''}

      <div class="phase-actions">
        <button class="btn primary" id="btn-after-heritage">CONTINUE →</button>
      </div>
    </div>
  `;
}

function wireSpeciesPhase() {
  // Heritage roll result screen — just needs a Continue button
  if (uiState.racialBackgroundResult) {
    document.getElementById('btn-after-heritage').addEventListener('click', () => {
      uiState.racialBackgroundResult = null;
      character.phase = 'background';
      saveCharacter();
      renderAll();
    });
    return;
  }

  // Shared apply logic — used by both double-click on card and the confirm button.
  async function applySelectedSpecies() {
    if (!uiState.selectedSpecies) return;
    const sp = SPECIES.find(s => s.id === uiState.selectedSpecies);
    if (sp?.racial_background_roll) {
      const response = await apiCall('/api/character/racial-background-roll', {});
      await applyResponse(response);
      uiState.racialBackgroundResult = response;
      renderStage();
      return;
    }
    const response = await apiCall('/api/character/apply-species', { species_id: uiState.selectedSpecies });
    await applyResponse(response);
    character.phase = 'background';
    saveCharacter();
    renderAll();
  }

  document.querySelectorAll('[data-species]').forEach(card => {
    // Single click → highlight + preview traits panel.
    // We debounce the re-render (150ms) so that a double-click can cancel it
    // before it strips the old event listeners from the DOM.
    let clickTimer = null;
    card.addEventListener('click', () => {
      uiState.selectedSpecies = card.dataset.species;
      clearTimeout(clickTimer);
      clickTimer = setTimeout(() => renderStage(), 180);
    });
    // Double click → cancel pending single-click render, apply immediately
    card.addEventListener('dblclick', async () => {
      clearTimeout(clickTimer);
      uiState.selectedSpecies = card.dataset.species;
      await applySelectedSpecies();
    });
  });
  document.getElementById('btn-back-stats').addEventListener('click', () => {
    character.phase = 'society';
    saveCharacter();
    renderAll();
  });
  document.getElementById('btn-apply-species').addEventListener('click', applySelectedSpecies);
}

// ============================================================
// PHASE 3: Background Skills
// ============================================================

function renderBackgroundPhase() {
  const eduDm = charDM(character.characteristics.EDU);
  const allowed = Math.max(0, eduDm + 3);
  const selected = uiState.selectedBgSkills;

  // Load skill list from bootstrap (we'll fetch lazily)
  const baseBgSkills = ['Admin', 'Animals', 'Art', 'Athletics', 'Carouse', 'Drive', 'Electronics',
    'Flyer', 'Language', 'Mechanic', 'Medic', 'Profession', 'Science', 'Seafarer',
    'Streetwise', 'Survival', 'Vacc Suit'];
  // Merge in any species-specific extra background skills (e.g. Caprisap → Astrogation)
  const speciesDef = SPECIES.find(s => s.id === character.species_id);
  const extraBgSkills = (speciesDef && speciesDef.extra_background_skills) || [];
  const bgSkills = [...new Set([...baseBgSkills, ...extraBgSkills])].sort();

  // For cascade skills that need a specialty, track which one is expanded
  const expandedCascade = uiState.bgExpandedCascade || null;

  const chips = bgSkills.map(skill => {
    const isCascade = !!CASCADE_SKILLS[skill];
    // A cascade skill can be "selected" as any of its specialties
    const selectedVariant = [...selected].find(s => s === skill || s.startsWith(skill + ' ('));
    const isSelected = !!selectedVariant;
    const isExpanded = expandedCascade === skill;
    const disabled = !isSelected && !isExpanded && selected.size >= allowed;

    let subChips = '';
    if (isCascade && isExpanded) {
      subChips = `<div class="bg-specialty-row">${(CASCADE_SKILLS[skill] || []).map(sp => {
        const fullName = `${skill} (${sp})`;
        const spSelected = selected.has(fullName);
        return `<button class="skill-chip specialty-chip ${spSelected ? 'selected' : ''}" data-bg-specialty="${escapeHTML(fullName)}">${escapeHTML(sp)}</button>`;
      }).join('')}</div>`;
    }

    return `
      <div class="bg-skill-wrap" style="display:inline-block">
        <button class="skill-chip ${isSelected ? 'selected' : ''} ${isCascade ? 'cascade' : ''} ${isExpanded ? 'expanded-cascade' : ''}" data-skill="${skill}" ${disabled ? 'disabled' : ''}>
          ${skill}${isCascade ? (isExpanded ? ' ▾' : ' ▸') : ''}
        </button>
        ${subChips}
      </div>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 03 — BACKGROUND SKILLS</span></div>
    <div class="stage-content">
      <div class="phase-label">Adolescence · Pre-Career</div>
      <h2 class="phase-title">Formative Years</h2>
      <p class="phase-subtitle">Skills picked up during your upbringing, before the universe happened to you.</p>

      <div class="phase-body">
        <p>Your <strong>Education DM</strong> is <strong>${formatDM(eduDm)}</strong>, so you get <strong>${allowed}</strong> background skill${allowed === 1 ? '' : 's'} at level 0. Think about where your Traveller grew up — an agri-world? An asteroid belt? A starport slum? Pick skills that tell that story.</p>
        ${extraBgSkills.length ? `<p style="font-size:12px;color:var(--amber);margin-top:6px">★ <strong>${speciesDef.name}</strong> trait: ${extraBgSkills.join(', ')} added to the available list (Natural Starfarers).</p>` : ''}
      </div>

      <div class="skill-picker">${chips}</div>
      <div class="picker-status">SELECTED ${selected.size} / ${allowed}</div>

      <div class="phase-actions">
        <button class="btn ghost" id="btn-back-species">← BACK</button>
        <button class="btn primary" id="btn-confirm-bg" ${selected.size === allowed ? '' : 'disabled'}>
          CONFIRM BACKGROUND →
        </button>
        <button class="btn" id="btn-skip-bg" ${allowed > 0 ? 'disabled' : ''}>
          SKIP (NO SKILLS)
        </button>
      </div>
    </div>
  `;
}

function wireBackgroundPhase() {
  document.querySelectorAll('[data-skill]').forEach(chip => {
    chip.addEventListener('click', () => {
      const skill = chip.dataset.skill;
      const isCascade = !!CASCADE_SKILLS[skill];

      if (isCascade) {
        // Remove any previously selected variant of this cascade skill
        const existing = [...uiState.selectedBgSkills].find(s => s === skill || s.startsWith(skill + ' ('));
        if (existing) {
          // Already selected — deselect and re-render
          uiState.selectedBgSkills.delete(existing);
          renderStage();
          return;
        }
        // Show the full-screen specialty overlay (same as career event cascade picks)
        uiState.pendingSkillGrant = { skillName: skill, level: 0 };
        _skillGrantCallback = (fullText) => {
          // fullText = "Electronics (Computers) 0" — strip the trailing level digit
          const nameOnly = fullText.replace(/\s+\d+\s*$/, '').trim();
          uiState.selectedBgSkills.add(nameOnly);
          renderStage();
        };
        renderStage();
        return;
      } else {
        if (uiState.selectedBgSkills.has(skill)) {
          uiState.selectedBgSkills.delete(skill);
        } else {
          uiState.selectedBgSkills.add(skill);
        }
      }
      renderStage();
    });
  });

  // Specialty chips inside expanded cascade skills
  document.querySelectorAll('[data-bg-specialty]').forEach(chip => {
    chip.addEventListener('click', () => {
      const fullName = chip.dataset.bgSpecialty; // e.g. "Electronics (Computers)"
      const parentSkill = fullName.split(' (')[0];
      // Remove any other variant of the same parent already selected
      const existing = [...uiState.selectedBgSkills].find(s => s === parentSkill || s.startsWith(parentSkill + ' ('));
      if (existing) uiState.selectedBgSkills.delete(existing);
      // Select this specialty
      uiState.selectedBgSkills.add(fullName);
      uiState.bgExpandedCascade = null;
      renderStage();
    });
  });
  document.getElementById('btn-back-species').addEventListener('click', () => {
    character.phase = 'species';
    saveCharacter();
    renderAll();
  });
  document.getElementById('btn-confirm-bg').addEventListener('click', async () => {
    const chosen = Array.from(uiState.selectedBgSkills);
    try {
      const response = await apiCall('/api/character/background-skills', { chosen });
      await applyResponse(response);
      renderAll();
    } catch (e) { alert(e.message); }
  });
  const skipBtn = document.getElementById('btn-skip-bg');
  if (skipBtn) {
    skipBtn.addEventListener('click', async () => {
      const response = await apiCall('/api/character/background-skills', { chosen: [] });
      await applyResponse(response);
      renderAll();
    });
  }
}

// ============================================================
// PHASE 3.5: Pre-Career Education (optional)
// ============================================================

const PRE_CAREER_SERVICES = [
  { id: 'army',   name: 'Military Academy — Army',    career_id: 'army',
    desc: 'Officer track for the ground forces. Tough qualification, solid pay.' },
  { id: 'marine', name: 'Military Academy — Marines', career_id: 'marine',
    desc: 'Hardest qualification target. Commissioned marines lead boarding actions.' },
  { id: 'navy',   name: 'Military Academy — Navy',    career_id: 'navy',
    desc: 'The prestige track. INT-based qualification, ship-bound officer career.' },
];

function renderPreCareerPhase() {
  const status = character.pre_career_status || {};
  const stage = status.stage || 'none';

  // Skill picker screen — shown after enrollment (level 0) or graduation (level 1)
  if (uiState.lastRoll?.type === 'precareer_skill_pick') {
    const remaining = status.skill_picks_remaining || 0;
    const pool = status.skill_pool || [];
    const pickLevel = status.skill_pick_level ?? 1;
    const pickStage = status.skill_pick_stage ?? 'graduation';
    const stageLabel = pickStage === 'enrollment' ? 'Enrollment Skills' : 'Graduation Skills';
    const levelLabel = pickLevel === 0 ? 'level 0 (your majors — you can raise them later)' : 'level 1';
    const picked = Array.from(uiState.selectedPreCareerSkills || new Set());
    const awaitingSpec = uiState.pcSkillSpecialtyPick; // skill name pending specialty
    const picker = pool.map(s => {
      const hasSpec = !!(SKILLS_DATA.speciality && SKILLS_DATA.speciality[s]);
      // A skill with specialties is "selected" if any picked entry starts with "s ("
      const sel = hasSpec
        ? picked.some(p => p === s || p.startsWith(s + ' ('))
        : picked.includes(s);
      const isAwaiting = awaitingSpec === s;
      return `<button class="skill-chip ${sel ? 'selected' : ''} ${isAwaiting ? 'awaiting-spec' : ''}"
        data-pc-skill="${escapeHTML(s)}"
        ${!sel && !isAwaiting && picked.length >= remaining ? 'disabled' : ''}
        >${escapeHTML(s)}${hasSpec ? ' ▾' : ''}</button>`;
    }).join('');
    // Specialty sub-picker — appears when user clicked a skill that needs one
    const specPickerHTML = awaitingSpec ? (() => {
      const specs = SKILLS_DATA.speciality[awaitingSpec] || [];
      const chips = specs.map(sp =>
        `<button class="specialty-chip" data-pc-specialty="${escapeHTML(awaitingSpec)}" data-spec="${escapeHTML(sp)}">${escapeHTML(sp)}</button>`
      ).join('');
      return `<div class="specialty-picker-box">
        <div class="specialty-picker-label">CHOOSE SPECIALITY FOR ${escapeHTML(awaitingSpec).toUpperCase()}</div>
        ${chips}
      </div>`;
    })() : '';
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">${escapeHTML(stageLabel)}</div>
        <h2 class="phase-title">Pick ${remaining} Skill${remaining === 1 ? '' : 's'}</h2>
        <p class="phase-body">Choose <strong>${remaining}</strong> skill${remaining === 1 ? '' : 's'} at <strong>${levelLabel}</strong>.</p>
        <div class="skill-picker">${picker}</div>
        ${specPickerHTML}
        <div class="phase-actions">
          <button class="btn primary" id="btn-confirm-pc-skills"
            ${picked.length !== remaining ? 'disabled' : ''}>
            ${picked.length === remaining ? `CONFIRM ${remaining}/${remaining} →` : `PICK ${remaining - picked.length} MORE`}
          </button>
        </div>
      </div>
    `;
  }

  // Post-roll view: show the qualification roll outcome
  if (uiState.lastRoll?.type === 'precareer_qualify') {
    const lr = uiState.lastRoll;
    const passed = lr.passed;
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Qualification Roll — ${lr.trackName}</div>
        <h2 class="phase-title">${passed ? 'Qualified' : 'Did Not Qualify'}</h2>
        ${rollReadoutHTML(lr.data, { label: `${lr.charLabel} ${lr.target}+` })}
        ${lr.enrollmentApplied?.length ? `
          <div class="dm-applied-box">
            <span class="event-label">Enrollment bonus</span>
            ${lr.enrollmentApplied.map(s => `<div class="dm-chip applied">${escapeHTML(s)}</div>`).join('')}
          </div>
        ` : ''}
        <p class="phase-body">${passed
          ? `Enrolled. ${lr.ageCost ? `${lr.ageCost} years pass while you study — one event per year, then graduation.` : 'Now roll events and then graduation.'}`
          : `Didn't meet the bar. You skip straight to your first career without any education bonus.`
        }</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-precareer-qualify">
            ${passed ? 'BEGIN STUDIES →' : 'CONTINUE TO CAREER →'}
          </button>
        </div>
      </div>
    `;
  }

  // Post-roll view: graduation outcome (event already rolled, shown inline)
  if (uiState.lastRoll?.type === 'precareer_graduate') {
    const lr = uiState.lastRoll;
    const labels = { pass: 'Graduated', honours: 'Graduated with Honours', fail: 'Failed to Graduate' };
    const ev = lr.event || {};
    const appliedHTML = lr.applied?.length ? `
      <div class="dm-applied-box">
        <span class="event-label">Graduation benefits</span>
        ${lr.applied.map(s => `<div class="dm-chip applied">${escapeHTML(s)}</div>`).join('')}
      </div>
    ` : '';
    const eventHTML = `
      <div class="event-box">
        <span class="event-label">Education Event [2D=${ev.roll?.total ?? '?'}]</span>
        ${escapeHTML(ev.event_text || 'Nothing remarkable happens.')}
      </div>
      ${ev.auto_applied?.length ? `
        <div class="dm-applied-box">
          <span class="event-label">Auto-applied</span>
          ${ev.auto_applied.map(s => `<div class="dm-chip applied">${escapeHTML(s)}</div>`).join('')}
        </div>` : ''}
      ${ev.forced_fail ? `<p class="phase-body" style="color:var(--danger)">This event overrides your graduation — you fail to graduate.</p>` : ''}
    `;
    const hasPicks = (status.skill_picks_remaining || 0) > 0;
    const pendingAnySkill = !!ev.pending_any_skill;
    const pendingEvent10 = !!ev.pending_event10;
    const pendingEvent11 = !!ev.pending_event11;
    const pendingLifeEvent = !!ev.pending_life_event;
    const lifeEventChoiceKind = ev.life_event_choice_kind || null;
    const pendingInjury = !!ev.pending_injury;
    const injuryData = ev.injury_pending_data || character.pending_injury_choice || null;
    const nextBtn = pendingEvent11
      ? `<button class="btn primary" id="btn-show-event11">RESPOND TO DRAFT →</button>`
      : pendingEvent10
        ? `<button class="btn primary" id="btn-show-event10">TAKE TUTOR CHALLENGE →</button>`
        : (pendingInjury || character.pending_injury_choice)
          ? `<button class="btn primary" id="btn-show-injury-choice">RESOLVE INJURY →</button>`
          : pendingLifeEvent
            ? `<button class="btn primary" id="btn-show-life-event-choice">RESOLVE LIFE EVENT →</button>`
            : pendingAnySkill
              ? `<button class="btn primary" id="btn-show-any-skill-pick">CHOOSE EVENT SKILL →</button>`
              : hasPicks
                ? `<button class="btn primary" id="btn-start-skill-pick">PICK GRADUATION SKILLS →</button>`
                : `<button class="btn primary" id="btn-post-precareer-graduate">CONTINUE TO CAREER →</button>`;
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Graduation — ${labels[lr.outcome]}</div>
        <h2 class="phase-title">${labels[lr.outcome]}</h2>
        ${rollReadoutHTML(lr.data, { label: `${lr.charLabel} ${lr.target}+` })}
        ${appliedHTML}
        ${eventHTML}
        <p class="picker-status"><em>Apply any additional event effects manually.</em></p>
        <div class="phase-actions">${nextBtn}</div>
      </div>
    `;
  }

  // Injury stat choice screen — shown when pending_injury_choice is set
  if (uiState.lastRoll?.type === 'precareer_injury_choice') {
    const inj = character.pending_injury_choice || uiState.lastRoll.injuryData || {};
    const choices = inj.choices || ['STR', 'DEX', 'END'];
    const prompt = inj.prompt || 'Choose a physical characteristic to absorb the damage.';
    const title = inj.title || 'Injury';
    const dmgAmount = inj.damage_to_chosen ?? '?';
    const autoOthers = inj.auto_reduce_others || 0;

    const statDescriptions = { STR: 'Strength', DEX: 'Dexterity', END: 'Endurance' };
    const cards = choices.map(stat => `
      <button class="card" id="btn-injury-stat-${stat}">
        <div class="card-title">${stat} — ${statDescriptions[stat] || stat}</div>
        <div class="card-meta">Current: ${character.characteristics[stat] ?? '?'}</div>
        <div class="card-desc">Damage: −${dmgAmount}${autoOthers ? ` to ${stat}, −${autoOthers} to other two` : ''}. Next you choose: accept stat loss (free) OR pay medical debt to keep your stats intact.</div>
      </button>
    `).join('');

    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Injury — ${title}</div>
        <h2 class="phase-title">${title}</h2>
        <p class="phase-body">${prompt}</p>
        <p class="phase-body" style="color:var(--amber-dim);font-size:11px">Pick which stat absorbs the hit. You'll then choose: accept permanent stat loss (no cost) OR pay medical debt to keep stats intact.</p>
        <div class="card-grid">${cards}</div>
      </div>
    `;
  }

  // Treatment choice — shown after the player picks which stat is hit, before damage is applied
  if (uiState.lastRoll?.type === 'precareer_injury_treatment') {
    const tc = character.pending_injury_treatment_choice;
    if (!tc) {
      // Treatment already resolved or stale state — skip ahead
      uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_graduate' };
      renderStage();
      return '';
    }
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Injury — Treatment Decision</div>
        <h2 class="phase-title">How Will You Handle This?</h2>
        ${renderInjuryTreatmentChoiceHTML(tc, 'precareer-treatment')}
      </div>
    `;
  }

  // Life event interactive choice screen
  if (uiState.lastRoll?.type === 'precareer_life_event_choice') {
    const kind = uiState.lastRoll.choiceKind;
    const hasBenefitRolls = (character.pending_benefit_rolls || 0) > 0;

    let title, body, buttons;
    if (kind === 'romantic_split') {
      title = 'Life Event — Relationship Ends Badly';
      body = 'A romantic relationship involving you ends badly. Choose the consequence:';
      buttons = `
        <button class="card" id="btn-life-choice-rival">
          <div class="card-title">Rival [Romantic]</div>
          <div class="card-desc">They become a rival — someone who competes with or resents you.</div>
        </button>
        <button class="card" id="btn-life-choice-enemy">
          <div class="card-title">Enemy [Romantic]</div>
          <div class="card-desc">They become an enemy — actively working against you.</div>
        </button>`;
    } else if (kind === 'betrayal_no_associates') {
      title = 'Life Event — Betrayal';
      body = 'A friend has betrayed you. You have no existing Contacts or Allies to convert. Gain one of:';
      buttons = `
        <button class="card" id="btn-life-choice-rival">
          <div class="card-title">Rival [Betrayer]</div>
          <div class="card-desc">They become a rival — someone who resents or opposes you.</div>
        </button>
        <button class="card" id="btn-life-choice-enemy">
          <div class="card-title">Enemy [Betrayer]</div>
          <div class="card-desc">They become an active enemy — a serious, ongoing threat.</div>
        </button>`;
    } else if (kind === 'crime_choice') {
      title = 'Life Event — Crime';
      body = 'You commit or are accused of a crime. Choose your consequence:';
      buttons = `
        <button class="card ${hasBenefitRolls ? '' : 'locked'}" id="btn-life-choice-lose_benefit" ${hasBenefitRolls ? '' : 'disabled'}>
          <div class="card-title">Lose a Benefit Roll ${hasBenefitRolls ? '' : '(none available)'}</div>
          <div class="card-desc">You pay a fine or bribe. Lose one mustering-out benefit roll.</div>
        </button>
        <button class="card" id="btn-life-choice-prisoner">
          <div class="card-title">Take the Prisoner Career</div>
          <div class="card-desc">You serve time. Your next career must be Prisoner.</div>
        </button>`;
    } else {
      title = 'Life Event Choice';
      body = 'An unexpected event requires a decision.';
      buttons = '';
    }

    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Life Event — Choose</div>
        <h2 class="phase-title">${title}</h2>
        <p class="phase-body">${body}</p>
        <div class="card-grid">${buttons}</div>
      </div>
    `;
  }

  // Event 10 — tutor challenge skill picker
  if (uiState.lastRoll?.type === 'precareer_event10') {
    const lr = uiState.lastRoll;
    const pool = status.event10_skill_pool || [];
    const filter = uiState.event10Filter || '';
    const filtered = pool.filter(s => s.toLowerCase().includes(filter.toLowerCase()));
    const chips = filtered.map(s =>
      `<button class="skill-chip" data-event10-skill="${escapeHTML(s)}">${escapeHTML(s)}</button>`
    ).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Education Event 10 — Tutor Challenge</div>
        <h2 class="phase-title">Challenge Your Tutor</h2>
        <p class="phase-body">Pick a skill from your education curriculum, then roll 2D 9+. Success: +1 level in that skill and gain a Rival [Tutor].</p>
        <input class="skill-search" id="event10-skill-search" type="text" placeholder="Filter skills…" value="${escapeHTML(filter)}" autocomplete="off" />
        <div class="skill-picker">${chips}</div>
      </div>
    `;
  }

  // Event 11 — draft event: Drifter / Draft / Dodge
  if (uiState.lastRoll?.type === 'precareer_event11') {
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Education Event 11 — Draft!</div>
        <h2 class="phase-title">War Is Coming</h2>
        <p class="phase-body">A wide-ranging draft has been instigated. Choose your response:</p>
        <div class="card-grid">
          <button class="card" id="btn-event11-drifter">
            <div class="card-title">Flee — Drifter</div>
            <div class="card-desc">Avoid the draft by dropping out. You do not graduate. Your next career must be Drifter.</div>
          </button>
          <button class="card" id="btn-event11-draft">
            <div class="card-title">Accept the Draft</div>
            <div class="card-desc">Roll 1D: 1–3 Army, 4–5 Marine, 6 Navy. You do not graduate but enter that service directly.</div>
          </button>
          <button class="card" id="btn-event11-dodge">
            <div class="card-title">Pull Strings — Dodge (SOC 9+)</div>
            <div class="card-desc">Roll SOC 9+. Success: ignore the draft and continue to graduation. Failure: you do not graduate.</div>
          </button>
        </div>
      </div>
    `;
  }

  // Event 9 any-skill picker
  if (uiState.lastRoll?.type === 'precareer_any_skill_pick') {
    const lr = uiState.lastRoll;
    const filter = uiState.anySkillFilter || '';
    const filtered = ALL_SKILLS_NO_JOT.filter(s => s.toLowerCase().includes(filter.toLowerCase()));
    const chips = filtered.slice(0, 60).map(s =>
      `<button class="skill-chip" data-any-skill="${escapeHTML(s)}">${escapeHTML(s)}</button>`
    ).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Education Event — Free Skill</div>
        <h2 class="phase-title">Choose Any Skill (Level 0)</h2>
        <p class="phase-body">Pick any skill except Jack-of-All-Trades. It is gained at level 0.</p>
        <input class="skill-search" id="any-skill-search" type="text" placeholder="Filter skills…" value="${escapeHTML(filter)}" autocomplete="off" />
        <div class="skill-picker">${chips}</div>
      </div>
    `;
  }

  // Enrolled — always show graduate button immediately (events roll after graduation)
  if (stage === 'enrolled') {
    const track = status.track;
    const service = status.service;
    const trackName = trackDisplayName(track, service, status);
    const gradHint = trackGradHint(track);

    if (track === 'psionic_community' && status.pending_psionic_training) {
      const trainedTalents = character.psi_trained_talents || [];
      const talentsHTML = ['telepathy','clairvoyance','telekinesis','awareness','teleportation'].map(id => {
        const trained = trainedTalents.includes(id);
        const label = id.charAt(0).toUpperCase() + id.slice(1);
        return `<button class="btn ${trained ? 'ghost' : ''}" data-pc-psi-talent="${id}" ${trained ? 'disabled' : ''}>${trained ? '✓ ' : ''}${label}${trained ? '' : ' — free'}</button>`;
      }).join('');
      return `
        <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
        <div class="stage-content">
          <div class="phase-label">Enrolled · ${trackName}</div>
          <h2 class="phase-title">Psionic Training</h2>
          <p class="phase-body">Your community will train you at no cost. Train one or more talents, then graduate.</p>
          <div class="psi-talents">${talentsHTML}</div>
          <div class="phase-actions" style="margin-top:1rem">
            <button class="btn primary" id="btn-pc-graduate">ROLL GRADUATION</button>
          </div>
        </div>
      `;
    }

    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Enrolled · ${trackName}</div>
        <h2 class="phase-title">Time to Graduate</h2>
        <p class="phase-subtitle">${gradHint}</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-pc-graduate">ROLL GRADUATION</button>
        </div>
      </div>
    `;
  }

  // Track chosen but not yet qualified — show academy service picker if needed
  if (stage === 'choosing_service' && status.track === 'military_academy') {
    const cards = PRE_CAREER_SERVICES.map(s => `
      <button class="card" data-pc-service="${s.id}">
        <div class="card-title">${s.name}</div>
        <div class="card-desc">${s.desc}</div>
      </button>
    `).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Military Academy · Pick a Service</div>
        <h2 class="phase-title">Which Branch?</h2>
        <p class="phase-body">The academy you qualify into commits you to that service career. Commission on graduation means starting at Rank 1 instead of basic training.</p>
        <div class="card-grid">${cards}</div>
        <div class="phase-actions">
          <button class="btn" id="btn-pc-back-to-choose">← BACK</button>
        </div>
      </div>
    `;
  }

  // Merchant Academy: curriculum selection
  if (stage === 'choosing_curriculum' && status.track === 'merchant_academy') {
    const curricula = [
      { id: 'business', name: 'Business', desc: 'Commerce, brokerage, and trade. Enroll in the Broker skill table. Enter Merchant or Citizen at officer rank.' },
      { id: 'shipboard', name: 'Shipboard', desc: 'Freight hauling and ship operations. Enroll in the Merchant Marine skill table. Enter Merchant at officer rank.' },
    ];
    const cards = curricula.map(c => `
      <button class="card" data-pc-curriculum="${c.id}">
        <div class="card-title">${c.name}</div>
        <div class="card-desc">${c.desc}</div>
      </button>
    `).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Merchant Academy · Pick a Curriculum</div>
        <h2 class="phase-title">Which Programme?</h2>
        <p class="phase-body">INT 9+ to qualify (DM+1 if SOC 8+). 4 years. Graduate for +1 EDU and permanent advancement bonus in Merchant or Citizen.</p>
        <div class="card-grid">${cards}</div>
        <div class="phase-actions">
          <button class="btn" id="btn-pc-back-to-choose">← BACK</button>
        </div>
      </div>
    `;
  }

  // Default: pick a track
  // All tracks are always available — the homeworld/SOC restrictions are flavour-only notes,
  // not hard locks. (Previously gated; now open so players can always choose.)
  const hwUwp = character.homeworld_uwp || '';
  const hwTL = hwUwp.includes('-') ? parseInt(hwUwp.split('-').pop(), 16) : 99;
  const hwSize = hwUwp.length >= 2 ? parseInt(hwUwp[1], 16) : -1;
  const soc = character.characteristics?.SOC ?? 0;

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
    <div class="stage-content">
      <div class="phase-label">Optional · Age ${character.age}</div>
      <h2 class="phase-title">Education Before Service?</h2>
      <p class="phase-subtitle">Before picking a career, you can spend a few years in education. Or skip and go straight to the job.</p>

      <div class="card-grid">
        <button class="card" id="btn-pc-university">
          <div class="card-title">University</div>
          <div class="card-desc">INT 6+ to qualify, 4 years, +1 EDU on enrollment. Graduate for +2 EDU and 2 skills at level 1. Honours at 10+ adds SOC +1 and DM+1 to your first career qualification.</div>
        </button>
        <button class="card" id="btn-pc-academy">
          <div class="card-title">Military Academy</div>
          <div class="card-desc">3 years. Qualification varies by service. Pass graduation to roll Commission 8+ with DM+2 — success starts you at officer rank. Graduated with Honours means automatic Rank 1 commission.</div>
        </button>
        <button class="card" id="btn-pc-merchant-academy">
          <div class="card-title">Merchant Academy</div>
          <div class="card-desc">INT 9+ to qualify, 4 years. Choose Business or Shipboard curriculum. Graduate for +1 EDU and start Merchant/Citizen at officer rank with a permanent advancement bonus.</div>
        </button>
        <button class="card" id="btn-pc-colonial">
          <div class="card-title">Colonial Upbringing</div>
          <div class="card-desc">Typical for low-tech frontier worlds (TL 8 or less). Broad survival skills (Survival 1 + 10 skills at 0). Graduate for END+1, JoaT 1, but EDU−D3 and permanent qualification penalties.</div>
        </button>
        <button class="card" id="btn-pc-hard-knocks">
          <div class="card-title">School of Hard Knocks</div>
          <div class="card-desc">The street as classroom. Street smarts: Streetwise 1 + 2 skill picks. Graduate for Gun Combat 0 and 3 more skills, but DM−2 to commission in first career.</div>
        </button>
        <button class="card" id="btn-pc-spacer">
          <div class="card-title">Spacer Community</div>
          <div class="card-desc">Raised on an asteroid belt or orbital. INT 4+ to enroll. 3 years. Vacc Suit 1 + 2 picks. Graduate for DEX+1, Pilot 0, and DM+1 to Merchant (Free Trader) advancement.</div>
        </button>
        <button class="card" id="btn-pc-psionic">
          <div class="card-title">Psionic Community</div>
          <div class="card-desc">Tests PSI (if untested). Requires PSI 8+. 3 years. Psionic talent training during enrollment. Graduate for PSI+1 and permanent Psion career auto-entry.</div>
        </button>
        <button class="card" id="btn-pc-skip">
          <div class="card-title">Skip</div>
          <div class="card-desc">Age ${character.age} and hungry for a paycheck. Go straight to the career phase.</div>
        </button>
      </div>
    </div>
  `;
}

// Helper: human-readable track name from status
function trackDisplayName(track, service, status) {
  if (track === 'university') return 'University';
  if (track === 'military_academy') {
    return PRE_CAREER_SERVICES.find(s => s.id === service)?.name || 'Military Academy';
  }
  if (track === 'merchant_academy') {
    const curr = status?.curriculum_name || status?.curriculum || '';
    return curr ? `Merchant Academy (${curr})` : 'Merchant Academy';
  }
  const TRACK_NAMES = {
    colonial_upbringing: 'Colonial Upbringing',
    psionic_community: 'Psionic Community',
    school_of_hard_knocks: 'School of Hard Knocks',
    spacer_community: 'Spacer Community',
  };
  return TRACK_NAMES[track] || track;
}

// Helper: graduation hint text for enrolled view
function trackGradHint(track) {
  const HINTS = {
    university: 'Roll EDU 7+ to graduate (10+ for Honours). Then one education event.',
    military_academy: 'Roll INT 8+ to graduate (11+ for Honours). Then one education event.',
    merchant_academy: 'Roll INT 7+ to graduate (11+ for Honours). Then one education event.',
    colonial_upbringing: 'Roll INT 8+ to graduate (12+ for Honours, END 8+ gives DM+1). No age cost.',
    psionic_community: 'Roll PSI 6+ to graduate (12+ for Honours, INT 8+ gives DM+1). Then one education event.',
    school_of_hard_knocks: 'Roll INT 7+ to graduate (11+ for Honours, END 9+ gives DM+1). Then one education event.',
    spacer_community: 'Roll INT 8+ to graduate (12+ for Honours, DEX 6+ gives DM+1). Then one education event.',
  };
  return HINTS[track] || 'Roll for graduation — hit the honours target for even more.';
}

function wirePreCareerPhase() {
  // Helper: fire a simple pre-career qualify call and set lastRoll
  async function fireQualify(track, extraParams, trackName, charLabel, target, ageCost) {
    try {
      const response = await apiCall('/api/character/pre-career/qualify',
        { track, ...extraParams });
      await applyResponse(response);
      if (response.choosing_curriculum) { renderStage(); return; }
      // Automatic tracks (colonial, hard knocks) may not have a roll
      const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
      uiState.lastRoll = {
        type: hasPicks ? 'precareer_skill_pick' : 'precareer_qualify',
        data: response.roll || null,
        passed: response.passed ?? true,
        trackName,
        charLabel,
        target,
        ageCost: ageCost || 0,
        enrollmentApplied: response.enrollment_applied || [],
        // for automatic tracks that jump straight to skill picker
        psi: response.psi,
        psi_roll: response.psi_roll,
      };
      if (hasPicks) uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
      renderAll();
    } catch (e) { alert(e.message); }
  }

  // Main choice
  const uni = document.getElementById('btn-pc-university');
  if (uni) uni.addEventListener('click', () =>
    fireQualify('university', {}, 'University', 'INT', 6, 4)
  );

  const academy = document.getElementById('btn-pc-academy');
  if (academy) academy.addEventListener('click', () => {
    character.pre_career_status = {
      ...(character.pre_career_status || {}),
      track: 'military_academy',
      stage: 'choosing_service',
    };
    saveCharacter();
    renderStage();
  });

  const merchantAcademy = document.getElementById('btn-pc-merchant-academy');
  if (merchantAcademy) merchantAcademy.addEventListener('click', () => {
    character.pre_career_status = {
      ...(character.pre_career_status || {}),
      track: 'merchant_academy',
      stage: 'choosing_curriculum',
    };
    saveCharacter();
    renderStage();
  });

  const colonial = document.getElementById('btn-pc-colonial');
  if (colonial) colonial.addEventListener('click', () =>
    fireQualify('colonial_upbringing', {}, 'Colonial Upbringing', 'Auto', null, 0)
  );

  const hardKnocks = document.getElementById('btn-pc-hard-knocks');
  if (hardKnocks) hardKnocks.addEventListener('click', () =>
    fireQualify('school_of_hard_knocks', {}, 'School of Hard Knocks', 'Auto', null, 2)
  );

  const spacer = document.getElementById('btn-pc-spacer');
  if (spacer) spacer.addEventListener('click', () =>
    fireQualify('spacer_community', {}, 'Spacer Community', 'INT', 4, 3)
  );

  const psionic = document.getElementById('btn-pc-psionic');
  if (psionic) psionic.addEventListener('click', () =>
    fireQualify('psionic_community', {}, 'Psionic Community', 'PSI', 8, 3)
  );

  const skip = document.getElementById('btn-pc-skip');
  if (skip) skip.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/skip');
      await applyResponse(response);
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Military Academy service picker
  document.querySelectorAll('[data-pc-service]').forEach(card => {
    card.addEventListener('click', async () => {
      const service = card.dataset.pcService;
      const svc = PRE_CAREER_SERVICES.find(s => s.id === service);
      const charLabel = service === 'navy' ? 'INT' : 'END';
      const target = service === 'army' ? 8 : 9;
      try {
        const response = await apiCall('/api/character/pre-career/qualify',
          { track: 'military_academy', service });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'precareer_qualify',
          data: response.roll,
          passed: response.passed,
          trackName: svc?.name || 'Military Academy',
          charLabel,
          target,
          ageCost: 3,
          enrollmentApplied: response.enrollment_applied || [],
        };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  // Merchant Academy curriculum picker
  document.querySelectorAll('[data-pc-curriculum]').forEach(card => {
    card.addEventListener('click', async () => {
      const curriculum = card.dataset.pcCurriculum;
      try {
        const response = await apiCall('/api/character/pre-career/qualify',
          { track: 'merchant_academy', curriculum });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'precareer_qualify',
          data: response.roll,
          passed: response.passed,
          trackName: `Merchant Academy (${curriculum})`,
          charLabel: 'INT',
          target: 9,
          ageCost: 4,
          enrollmentApplied: response.enrollment_applied || [],
        };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  const backToChoose = document.getElementById('btn-pc-back-to-choose');
  if (backToChoose) backToChoose.addEventListener('click', () => {
    character.pre_career_status = {
      ...(character.pre_career_status || {}),
      track: null,
      stage: 'none',
    };
    saveCharacter();
    renderStage();
  });

  // Post-qualify continue button
  const postQualify = document.getElementById('btn-post-precareer-qualify');
  if (postQualify) postQualify.addEventListener('click', () => {
    const passed = uiState.lastRoll?.passed;
    if (passed) {
      // University enrollment: player picks 2 skills at level 0 before events
      const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
      if (hasPicks) {
        uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
        uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_skill_pick' };
        renderStage();
      } else {
        // Military academy or no enrollment picks — go straight to enrolled view
        uiState.lastRoll = null;
        renderStage();
      }
    } else {
      // Engine already set phase=career on failed qualification
      uiState.lastRoll = null;
      renderAll();
    }
  });

  // Graduation roll button — also auto-rolls the education event server-side
  const gradBtn = document.getElementById('btn-pc-graduate');
  if (gradBtn) gradBtn.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/graduate', { chosen_skills: [] });
      await applyResponse(response);
      const st = character.pre_career_status || {};
      const track = st.track;
      const service = st.service;
      const trackName = trackDisplayName(track, service, st);
      // Prefer server-supplied char_key/target (works for all tracks including PSI)
      const charLabel = response.char_key || (track === 'university' ? 'EDU' : 'INT');
      const target = response.target || (track === 'university' ? 7 : 8);
      uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
      uiState.lastRoll = {
        type: 'precareer_graduate',
        data: response.roll,
        outcome: response.outcome,
        applied: response.applied || [],
        event: response.event || null,
        trackName,
        charLabel,
        target,
      };
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Psionic community enrollment: free talent training buttons
  document.querySelectorAll('[data-pc-psi-talent]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const talent = btn.dataset.pcPsiTalent;
      try {
        const response = await apiCall('/api/character/psionics/train', { talent_id: talent });
        await applyResponse(response);
      } catch (e) { alert(e.message); }
      renderAll();
    });
  });

  // Event 9: show any-skill picker
  const showAnySkillBtn = document.getElementById('btn-show-any-skill-pick');
  if (showAnySkillBtn) showAnySkillBtn.addEventListener('click', () => {
    uiState.anySkillFilter = '';
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_any_skill_pick' };
    renderStage();
  });

  // Injury choice: navigate to injury stat picker
  const showInjuryBtn = document.getElementById('btn-show-injury-choice');
  if (showInjuryBtn) showInjuryBtn.addEventListener('click', () => {
    const inj = character.pending_injury_choice || uiState.lastRoll?.injury_pending_data;
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_injury_choice', injuryData: inj };
    renderStage();
  });

  // Injury stat buttons (pre-career)
  ['STR', 'DEX', 'END'].forEach(stat => {
    const btn = document.getElementById(`btn-injury-stat-${stat}`);
    if (btn) btn.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/injury-choice', { chosen_stat: stat });
        await applyResponse(response);
        if (response.treatment_choice_pending) {
          // Show treatment choice screen before finalizing
          uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_injury_treatment' };
          renderStage();
          return;
        }
        // After injury, check if life event choice is still pending
        const lr = uiState.lastRoll;
        if (character.pending_life_event_choice) {
          uiState.lastRoll = { ...lr, type: 'precareer_graduate', pending_injury: false };
        } else {
          const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
          uiState.lastRoll = hasPicks
            ? { ...lr, type: 'precareer_skill_pick' }
            : { ...lr, type: 'precareer_graduate', pending_injury: false };
        }
        renderStage();
      } catch (e) { alert(e.message); }
    });
  });

  // Pre-career injury treatment buttons (accept loss OR pay debt)
  wireInjuryTreatmentButtons('precareer-treatment', (resp, paid) => {
    const lr = uiState.lastRoll;
    if (character.pending_life_event_choice) {
      uiState.lastRoll = { ...lr, type: 'precareer_graduate', pending_injury: false };
    } else {
      const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
      uiState.lastRoll = hasPicks
        ? { ...lr, type: 'precareer_skill_pick' }
        : { ...lr, type: 'precareer_graduate', pending_injury: false };
    }
    renderStage();
  });

  // Life event choice: navigate to choice screen
  const showLifeEventBtn = document.getElementById('btn-show-life-event-choice');
  if (showLifeEventBtn) showLifeEventBtn.addEventListener('click', () => {
    const kind = character.pending_life_event_choice?.kind || uiState.lastRoll?.life_event_choice_kind;
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_life_event_choice', choiceKind: kind };
    renderStage();
  });

  // Life event choice buttons (rival / enemy / lose_benefit / prisoner)
  document.querySelectorAll('[id^="btn-life-choice-"]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const choice = btn.id.replace('btn-life-choice-', '');
      try {
        const response = await apiCall('/api/character/life-event-choice', { choice });
        await applyResponse(response);
        // After resolving, check if we can continue or need skill picks
        const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
        uiState.lastRoll = hasPicks
          ? { ...uiState.lastRoll, type: 'precareer_skill_pick', pending_life_event: false }
          : { ...uiState.lastRoll, type: 'precareer_graduate', event: { ...uiState.lastRoll?.event, pending_life_event: false } };
        renderStage();
      } catch (e) { alert(e.message); }
    });
  });

  // Event 10: show tutor challenge picker
  const showEvent10Btn = document.getElementById('btn-show-event10');
  if (showEvent10Btn) showEvent10Btn.addEventListener('click', () => {
    uiState.event10Filter = '';
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_event10' };
    renderStage();
  });

  // Event 10 search filter
  const event10Search = document.getElementById('event10-skill-search');
  if (event10Search) {
    event10Search.focus();
    event10Search.addEventListener('input', () => {
      uiState.event10Filter = event10Search.value;
      renderStage();
    });
  }

  // Event 10 skill chip click — roll 2D 9+ and resolve
  document.querySelectorAll('[data-event10-skill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const skill = chip.dataset.event10Skill;
      const applyEvent10 = async (skillText) => {
        try {
          const response = await apiCall('/api/character/pre-career/event10-skill', { skill_text: skillText });
          await applyResponse(response);
          const succeeded = response.roll?.succeeded;
          const msg = succeeded
            ? `Tutor challenge on ${skillText}: SUCCESS! Gained +1 level and Rival [Tutor].`
            : `Tutor challenge on ${skillText}: failed. No bonus.`;
          alert(msg);
          uiState.event10Filter = '';
          uiState.lastRoll = null;
          renderAll();
        } catch (e) { alert(e.message); }
      };
      if (!interceptCascadeSkill(skill, applyEvent10)) await applyEvent10(skill);
    });
  });

  // Event 11: show draft event screen
  const showEvent11Btn = document.getElementById('btn-show-event11');
  if (showEvent11Btn) showEvent11Btn.addEventListener('click', () => {
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_event11' };
    renderStage();
  });

  // Event 11 choice buttons
  const ev11Drifter = document.getElementById('btn-event11-drifter');
  if (ev11Drifter) ev11Drifter.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/event11-choice', { choice: 'drifter' });
      await applyResponse(response);
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });

  const ev11Draft = document.getElementById('btn-event11-draft');
  if (ev11Draft) ev11Draft.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/event11-choice', { choice: 'draft' });
      await applyResponse(response);
      const career = response.draft_career || 'unknown';
      const d6 = response.roll?.dice?.[0] ?? '?';
      alert(`Drafted! D6=${d6} — you must enter the ${career.toUpperCase()} career.`);
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });

  const ev11Dodge = document.getElementById('btn-event11-dodge');
  if (ev11Dodge) ev11Dodge.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/event11-choice', { choice: 'dodge' });
      await applyResponse(response);
      const roll = response.roll;
      const succeeded = roll?.succeeded;
      const msg = succeeded
        ? `Draft dodged! (SOC check: ${roll.total} vs 9+). Graduation stands.`
        : `Draft dodge failed (SOC check: ${roll.total} vs 9+). Did not graduate.`;
      alert(msg);
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Any-skill search filter
  const anySkillSearch = document.getElementById('any-skill-search');
  if (anySkillSearch) {
    anySkillSearch.focus();
    anySkillSearch.addEventListener('input', () => {
      uiState.anySkillFilter = anySkillSearch.value;
      renderStage();
    });
  }

  // Any-skill chip click — apply and advance
  document.querySelectorAll('[data-any-skill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const skill = chip.dataset.anySkill;
      const applyAnySkill = async (skillText) => {
        try {
          const response = await apiCall('/api/character/pre-career/any-skill', { skill_text: skillText });
          await applyResponse(response);
          const lr = uiState.lastRoll;
          const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
          uiState.anySkillFilter = '';
          if (hasPicks) {
            uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
            uiState.lastRoll = { ...lr, type: 'precareer_skill_pick', pending_any_skill: false };
          } else {
            uiState.lastRoll = { ...lr, type: 'precareer_graduate', event: { ...lr.event, pending_any_skill: false } };
          }
          renderStage();
        } catch (e) { alert(e.message); }
      };
      if (!interceptCascadeSkill(skill, applyAnySkill)) await applyAnySkill(skill);
    });
  });

  // Transition from graduation result screen to skill picker screen
  const startPickBtn = document.getElementById('btn-start-skill-pick');
  if (startPickBtn) startPickBtn.addEventListener('click', () => {
    uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_skill_pick' };
    renderStage();
  });

  // Skill picker chips — intercept specialty-requiring skills
  document.querySelectorAll('[data-pc-skill]').forEach(chip => {
    chip.addEventListener('click', () => {
      const skill = chip.dataset.pcSkill;
      if (!uiState.selectedPreCareerSkills) uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
      const hasSpec = !!(SKILLS_DATA.speciality && SKILLS_DATA.speciality[skill]);
      // De-select: remove any picked entry for this skill (bare or with specialty)
      const existingPick = [...uiState.selectedPreCareerSkills].find(p => p === skill || p.startsWith(skill + ' ('));
      if (existingPick) {
        uiState.selectedPreCareerSkills.delete(existingPick);
        if (uiState.pcSkillSpecialtyPick === skill) uiState.pcSkillSpecialtyPick = null;
        renderStage();
        return;
      }
      if (hasSpec) {
        // Open specialty sub-picker instead of immediately adding
        uiState.pcSkillSpecialtyPick = (uiState.pcSkillSpecialtyPick === skill) ? null : skill;
        renderStage();
        return;
      }
      uiState.selectedPreCareerSkills.add(skill);
      renderStage();
    });
  });

  // Specialty sub-picker chips
  document.querySelectorAll('[data-pc-specialty]').forEach(chip => {
    chip.addEventListener('click', () => {
      const skill = chip.dataset.pcSpecialty;
      const spec = chip.dataset.spec;
      if (!uiState.selectedPreCareerSkills) uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
      // Remove any prior pick for this skill
      const prior = [...uiState.selectedPreCareerSkills].find(p => p === skill || p.startsWith(skill + ' ('));
      if (prior) uiState.selectedPreCareerSkills.delete(prior);
      uiState.selectedPreCareerSkills.add(`${skill} (${spec})`);
      uiState.pcSkillSpecialtyPick = null;
      renderStage();
    });
  });

  // Confirm skill picks
  const confirmPc = document.getElementById('btn-confirm-pc-skills');
  if (confirmPc) confirmPc.addEventListener('click', async () => {
    const chosen = Array.from(uiState.selectedPreCareerSkills || []);
    if (chosen.length === 0) return;
    try {
      const response = await apiCall('/api/character/pre-career/choose-skills',
        { chosen_skills: chosen });
      await applyResponse(response);
      uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
      if (response.skill_pick_stage === 'enrollment' && response.skill_picks_remaining === 0) {
        // Enrollment picks done: stay in pre_career for events/graduation
        uiState.lastRoll = null;
        renderStage();
      } else if (response.has_more_rounds || response.new_picks_remaining > 0) {
        // Next round queued — stay in skill pick screen with updated pool/level
        uiState.lastRoll = { ...(uiState.lastRoll || {}), type: 'precareer_skill_pick' };
        renderStage();
      } else {
        // All done — phase is 'career'
        uiState.lastRoll = null;
        renderAll();
      }
    } catch (e) { alert(e.message); }
  });

  // Post-graduate continue — advance phase client-side (server stays in pre_career to show the page)
  const postGrad = document.getElementById('btn-post-precareer-graduate');
  if (postGrad) postGrad.addEventListener('click', () => {
    character.phase = 'career';
    saveCharacter();
    uiState.lastRoll = null;
    renderAll();
  });

  // Post-qualify continue — clear lastRoll and route by phase
  // (already handled above by btn-post-precareer-qualify, kept for clarity)
}

// ============================================================
// PHASE 4: Career Loop
// ============================================================

function renderCareerPhase() {
  const term = character.current_term;

  // After clicking a career card we POST /api/character/qualify, which
  // returns a roll result but does NOT create a current_term (the term
  // only starts once the user picks an assignment and hits BEGIN TERM).
  // So between those two clicks we have: term === null, subPhase === 'qualify'.
  // Route that state to renderQualifyResult so the dice + assignment
  // picker actually render.
  if (!term && uiState.subPhase === 'qualify' && uiState.lastRoll) {
    return renderQualifyResult();
  }
  if (term && uiState.subPhase === 'draft_result' && uiState.lastRoll?.type === 'draft') {
    return renderDraftResult();
  }

  // Anagathics interest: one-time setup screen. Shown whenever the player reaches career selection
  // without having set a preference yet (null/undefined). Guard is anagathicsPhaseDone only — we
  // intentionally show this regardless of whether it's first career entry or a mid-career selection.
  const anaInterest = character.anagathics_interest;
  if ((anaInterest === null || anaInterest === undefined) && !uiState.anagathicsPhaseDone) {
    return renderAnagathicsIntroScreen();
  }

  // Anagathics intercept: fires BEFORE every career selection — first career (after pre-career)
  // and every term thereafter. When continuing the same career, end_term (leaving=false) does NOT
  // clear current_term, so pendingNextTermAction being set is the signal we're in that state.
  // Skip the per-term prompt if player opted out.
  if (anaInterest !== 'no' && !uiState.anagathicsPhaseDone && (!term || uiState.pendingNextTermAction)) {
    return renderAnagathicsPrompt();
  }

  // No active term → career picker; active term → term loop.
  if (!term) {
    return renderChooseCareer();
  }
  return renderActiveTerm();
}

function renderChooseCareer() {
  const forcedId = character.forced_next_career_id || null;
  const banned = new Set(character.banned_career_ids || []);
  const soc = character.society_id || 'third_imperium';
  const speciesId = character.species_id || null;
  const speciesDef = SPECIES.find(s => s.id === speciesId) || null;
  const isCetacean = speciesId === 'dolphin' || speciesId === 'uplifted_orca';
  // Does this character have Vacc Suit skill at any level?
  const hasVaccSuit = (character.skills || []).some(s => (s.name || '').toLowerCase() === 'vacc suit' && s.level >= 1);
  const cetaceanBlockedCareers = new Set((speciesDef && speciesDef.blocked_careers) || []);

  const careerList = forcedId
    ? CAREERS.filter(c => c.id === forcedId)
    : CAREERS.filter(c => {
        if (banned.has(c.id)) return false;
        // "societies" = whitelist: only show for these societies
        if (c.societies && c.societies.length > 0 && !c.societies.includes(soc)) return false;
        // "blocked_societies" = blacklist: hide for these societies
        if (c.blocked_societies && c.blocked_societies.includes(soc)) return false;
        // "allowed_species" = species whitelist: only show for these species
        if (c.allowed_species && c.allowed_species.length > 0) {
          if (!speciesId || !c.allowed_species.includes(speciesId)) return false;
        }
        // "blocked_species" = species blacklist: hide for these species
        if (c.blocked_species && c.blocked_species.includes(speciesId)) return false;
        // Cetacean species: block careers flagged in their species JSON
        if (isCetacean && cetaceanBlockedCareers.has(c.id)) return false;
        // Cetacean species: non-cetacean-specific careers require Vacc Suit first
        if (isCetacean && (!c.allowed_species || c.allowed_species.length === 0) && !hasVaccSuit) return false;
        return true;
      });
  const forcedCareerName = forcedId ? (CAREERS.find(c => c.id === forcedId)?.name || forcedId.toUpperCase()) : null;
  const forcedBanner = forcedId ? `
    <p class="phase-body" style="color:var(--danger);font-weight:bold">
      ⚠ You must enter the <strong>${forcedCareerName}</strong> career this term — this is mandatory.
    </p>` : '';
  const bannedBanner = banned.size && !forcedId ? `
    <p class="phase-body" style="color:var(--amber-dim);font-size:11px">
      Banned from re-entry: ${[...banned].map(id => id.toUpperCase()).join(', ')}
    </p>` : '';
  const vaccLockBanner = isCetacean && !hasVaccSuit && !forcedId ? `
    <p class="phase-body" style="color:var(--amber);font-size:11px">
      🐬 Cetacean restriction: core careers are unavailable until you have the <strong>Vacc Suit</strong> skill.
      Gain it through a cetacean career first, then core careers will unlock.
    </p>` : '';

  const cards = careerList.map(c => {
    const isComplete = c.complete;
    const qual = c.qualification || {};
    let qualText;
    if (qual.automatic) {
      qualText = 'AUTO';
    } else if (qual.characteristic === 'DEX_OR_INT') {
      qualText = `DEX or INT ${qual.target}+`;
    } else {
      qualText = `${qual.characteristic} ${qual.target}+`;
    }
    const classes = ['card'];
    if (!isComplete) classes.push('partial');
    return `
      <button class="${classes.join(' ')}" data-career="${c.id}">
        <div class="card-title">${c.name}</div>
        <div class="card-meta">${qualText}${qual.auto_qualify_if?.SOC ? ` · AUTO@SOC≥${qual.auto_qualify_if.SOC.replace('>=','')}` : ''}</div>
        <div class="card-desc">${c.description}</div>
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 04 — CAREER SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Term ${character.total_terms + 1} · Age ${character.age}</div>
      <h2 class="phase-title">Choose a Career</h2>
      ${forcedBanner}
      ${bannedBanner}
      ${vaccLockBanner}
      <p class="phase-subtitle">${character.total_terms === 0
        ? 'Your first career defines the first four years of your adult life.'
        : 'You survived. Another four years await — continue, or try something new.'}</p>

      <div class="card-grid">${cards}</div>

      <p class="empty" style="font-size:11px;margin-top:8px">
        Careers marked <strong style="color:var(--amber-dim)">PARTIAL</strong> have basic qualification/survival/advancement rules
        encoded, but events/mishaps/skill tables are not yet filled in. See the README for how to complete them.
      </p>

      ${character.total_terms > 0 ? `
        <div class="phase-actions">
          <button class="btn" id="btn-finish-creation">FINISH CHARACTER CREATION →</button>
        </div>
      ` : ''}
    </div>
  `;
}

function wireCareerPhase() {
  // Choose career view
  document.querySelectorAll('[data-career]').forEach(card => {
    card.addEventListener('click', async () => {
      const careerId = card.dataset.career;
      uiState.selectedCareer = careerId;
      uiState.selectedAssignment = null;
      uiState.subPhase = 'qualify';
      // Consume forced_next_career_id so it doesn't restrict future terms.
      if (character.forced_next_career_id) {
        character.forced_next_career_id = null;
        saveCharacter();
      }
      const response = await apiCall('/api/character/qualify', { career_id: careerId });
      await applyResponse(response);
      uiState.lastRoll = response;
      renderAll();
    });
  });

  const finishBtn = document.getElementById('btn-finish-creation');
  if (finishBtn) {
    finishBtn.addEventListener('click', () => {
      character.phase = 'mustering';
      saveCharacter();
      renderAll();
    });
  }

  // Failed-qualification fallback options
  const btnDraft = document.getElementById('btn-accept-draft');
  if (btnDraft) {
    btnDraft.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/draft');
        await applyResponse(response);
        uiState.selectedCareer = response.career_id;
        uiState.selectedAssignment = response.assignment_id;
        uiState.subPhase = 'draft_result';
        uiState.lastRoll = {
          type: 'draft',
          roll: response.roll,
          career_name: response.career_name,
          assignment_name: response.assignment_name,
        };
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }

  const btnDrifter = document.getElementById('btn-drifter-auto');
  if (btnDrifter) {
    btnDrifter.addEventListener('click', async () => {
      uiState.selectedCareer = 'drifter';
      uiState.selectedAssignment = null;
      uiState.subPhase = 'qualify';
      const response = await apiCall('/api/character/qualify', { career_id: 'drifter' });
      await applyResponse(response);
      uiState.lastRoll = response;
      renderAll();
    });
  }

  const btnBeginDrafted = document.getElementById('btn-begin-drafted-term');
  if (btnBeginDrafted) {
    btnBeginDrafted.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'train';
      renderAll();
    });
  }

  // Active term view
  const btnAssign = document.getElementById('btn-start-term');
  if (btnAssign) {
    btnAssign.addEventListener('click', async () => {
      if (!uiState.selectedAssignment) return;
      const body = {
        career_id: uiState.selectedCareer,
        assignment_id: uiState.selectedAssignment,
      };
      // SolSec Secret Agent: pass the chosen cover career
      if (uiState.selectedCoverCareer) {
        body.cover_career_id = uiState.selectedCoverCareer;
      }
      const response = await apiCall('/api/character/start-term', body);
      await applyResponse(response);
      if (response.academy_commission_roll) {
        uiState.academyCommissionRoll = response.academy_commission_roll;
      }
      if (response.basic_training_skills) {
        uiState.basicTrainingSkills = response.basic_training_skills;
      }
      uiState.selectedCoverCareer = null;  // consumed
      uiState.subPhase = 'train';
      renderAll();
    });
  }

  document.querySelectorAll('[data-assignment]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedAssignment = card.dataset.assignment;
      // Reset cover career when switching assignments
      if (!(uiState.selectedCareer === 'solsec' && uiState.selectedAssignment === 'secret_agent')) {
        uiState.selectedCoverCareer = null;
      }
      renderStage();
    });
  });

  // SolSec Secret Agent: cover career picker
  document.querySelectorAll('[data-cover-career]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedCoverCareer = card.dataset.coverCareer;
      renderStage();
    });
  });

  // Home Forces Reserves: enroll / leave
  const btnHfEnroll = document.getElementById('btn-hf-enroll');
  if (btnHfEnroll) {
    btnHfEnroll.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/home-forces', {
          action: 'enroll',
          career_id: uiState.selectedCareer || character.current_term?.career_id || null,
        });
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'home_forces_training',
          roll: response.training_roll,
          result: response.training_result,
          component: response.component,
          auto_skill: response.auto_skill,
          rank_transferred: response.rank_transferred,
        };
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
  const btnHfLeave = document.getElementById('btn-hf-leave');
  if (btnHfLeave) {
    btnHfLeave.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/home-forces', { action: 'leave' });
        await applyResponse(response);
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }

  // Home Forces training banner dismiss
  const btnHfDismiss = document.getElementById('btn-hf-training-dismiss');
  if (btnHfDismiss) {
    btnHfDismiss.addEventListener('click', () => {
      uiState.lastRoll = null;
      renderStage();
    });
  }

  // SolSec Monitor: join / leave
  const btnMonitorJoin = document.getElementById('btn-monitor-join');
  if (btnMonitorJoin) {
    btnMonitorJoin.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/solsec-monitor', { active: true });
        await applyResponse(response);
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
  const btnMonitorLeave = document.getElementById('btn-monitor-leave');
  if (btnMonitorLeave) {
    btnMonitorLeave.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/solsec-monitor', { active: false });
        await applyResponse(response);
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }

  document.querySelectorAll('[data-skill-table]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tableKey = btn.dataset.skillTable;
      try {
        const response = await apiCall('/api/character/skill-roll', { table_key: tableKey });
        await applyResponse(response);
        const tableName = (CAREERS.find(c => c.id === character.current_term?.career_id)
                            ?.skill_tables?.[tableKey]?.name) || tableKey;
        uiState.lastRoll = {
          type: 'skill',
          data: response.roll,
          tableName,
          result: response.result,
          applied: response.applied,
        };
        // Check if the result is a bare cascade skill that needs specialty selection
        const bareSkill = (response.result || '').trim();
        if (CASCADE_SKILLS[bareSkill]) {
          uiState.pendingCareerSpecialty = {
            skillName: bareSkill,
            level: 1,
            tableKey,
            rollData: response.roll,
            result: response.result,
            applied: response.applied,
          };
        } else {
          uiState.pendingCareerSpecialty = null;
        }
        // Stay on 'train' subPhase so the user sees the 1D result
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  });

  // Helper: determine next sub-phase after training ends.
  // Anagathics is now offered BEFORE career selection, so training always leads straight to survival.
  function postTrainingSubPhase() {
    return 'survive';
  }

  const btnPostSkill = document.getElementById('btn-post-skill');
  if (btnPostSkill) {
    btnPostSkill.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.pendingCareerSpecialty = null;
      uiState.subPhase = postTrainingSubPhase();
      renderStage();
    });
  }

  // Career specialty picker (fired when a bare cascade skill is rolled, e.g. "Electronics")
  document.querySelectorAll('[data-career-specialty]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const spec = chip.dataset.careerSpecialty;
      const pending = uiState.pendingCareerSpecialty;
      if (!pending) return;
      try {
        // Apply the specialty via grant_event_skill — reuses existing endpoint
        const resp = await apiCall('/api/character/apply-specialty', {
          skill_text: `${pending.skillName} (${spec}) 1`,
        });
        await applyResponse(resp);
        uiState.pendingCareerSpecialty = null;
        // Update the lastRoll to show the fully resolved skill
        if (uiState.lastRoll) {
          uiState.lastRoll.applied = `+1 ${pending.skillName} (${spec}) (level 1)`;
        }
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  const btnBasicTrainingContinue = document.getElementById('btn-basic-training-continue');
  if (btnBasicTrainingContinue) {
    btnBasicTrainingContinue.addEventListener('click', () => {
      uiState.basicTrainingSkills = null;
      uiState.subPhase = postTrainingSubPhase();
      renderStage();
    });
  }

  const btnSurvive = document.getElementById('btn-survive');
  if (btnSurvive) {
    btnSurvive.addEventListener('click', async () => {
      const response = await apiCall('/api/character/survive');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'survive',
        data: response.roll,
        outcome: response.survived ? 'pass' : 'fail',
        parallel_event: response.parallel_event || null,
        anagathics_second_roll: response.anagathics_second_roll || null,
      };
      // Stay on 'survive' subPhase so dice readout renders before advancing
      renderAll();
    });
  }

  const btnPostSurvive = document.getElementById('btn-post-survive');
  if (btnPostSurvive) {
    btnPostSurvive.addEventListener('click', () => {
      // Use lastRoll outcome if available; fall back to server-side survived flag.
      const survived = uiState.lastRoll?.outcome === 'pass'
                    || (uiState.lastRoll?.outcome == null && character.current_term?.survived === true);
      uiState.lastRoll = null;
      uiState.subPhase = survived ? 'event' : 'mishap';
      renderStage();
    });
  }

  const btnEvent = document.getElementById('btn-event');
  if (btnEvent) {
    btnEvent.addEventListener('click', async () => {
      const response = await apiCall('/api/character/event');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'event',
        data: response.roll,
        eventText: response.event,
        dmGrants: response.dm_grants || [],
        statBonuses: response.stat_bonuses || [],
        autoPromotion: response.auto_promotion || null,
        associateOpsDone: [],
      };

      // Auto-add unambiguous single Ally grants without requiring the picker.
      // "Allies should always be added to the associates" — only skip if
      // quantity ops are present (D3 Allies etc.) since those need a die roll
      // to determine count.
      const rawAssocOpsForEvent = parseEventAssociateOps(response.event || '');
      const hasQuantityOps = rawAssocOpsForEvent.some(op => op.type === 'quantity');
      if (!hasQuantityOps) {
        for (let rawIdx = 0; rawIdx < rawAssocOpsForEvent.length; rawIdx++) {
          const op = rawAssocOpsForEvent[rawIdx];
          if (op.type === 'add' && op.kinds.length === 1 && op.kinds[0] === 'ally') {
            try {
              const allyResp = await apiCall('/api/character/associate', { op: 'add', kind: 'ally', description: '' });
              await applyResponse(allyResp);
              const done = uiState.lastRoll.associateOpsDone;
              while (done.length <= rawIdx) done.push(null);
              done[rawIdx] = 'Ally auto-added to Associates';
            } catch (_e) { /* silently ignore — ally was at least flagged */ }
          }
        }
      }

      // Stay on 'event' so the dice + event text render together
      renderAll();
    });
  }

  const btnPostEvent = document.getElementById('btn-post-event');
  if (btnPostEvent) {
    btnPostEvent.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'advance';
      renderStage();
    });
  }

  // Prisoner event 7 parole — leave career immediately on success.
  const btnParole = document.getElementById('btn-prisoner-parole');
  if (btnParole) {
    btnParole.addEventListener('click', async () => {
      await endTermWithAgingIntercept(true, 'parole', { type: 'muster_out' });
    });
  }

  // Citizen event 8 — retroactive survival failure → trigger mishap flow.
  const btnCitizenEv8Mishap = document.getElementById('btn-citizen-ev8-mishap');
  if (btnCitizenEv8Mishap) {
    btnCitizenEv8Mishap.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'mishap';
      renderAll();
    });
  }

  // "Roll on the Mishap Table" event (non-ejecting disaster): roll the mishap
  // inline and display the result right inside the event panel.
  const btnForcedMishap = document.getElementById('btn-event-forced-mishap');
  if (btnForcedMishap) {
    btnForcedMishap.addEventListener('click', async () => {
      btnForcedMishap.disabled = true;
      try {
        const response = await apiCall('/api/character/mishap');
        await applyResponse(response);
        if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
          uiState.lastRoll.mishapFromEvent = {
            total: response.roll?.total,
            text: response.mishap,
            frozenWatch: response.frozen_watch || false,
          };
        }
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not roll the mishap table.');
        btnForcedMishap.disabled = false;
      }
    });
  }

  // Event-choice skill picker: clicking a chip applies the chosen skill.
  const disableAllEventChips = () => {
    document.querySelectorAll('[data-event-skill],[data-event-dm],[data-event-transfer]').forEach(c => { c.disabled = true; });
  };
  const enableAllEventChips = () => {
    document.querySelectorAll('[data-event-skill],[data-event-dm],[data-event-transfer]').forEach(c => { c.disabled = false; });
  };
  document.querySelectorAll('[data-event-skill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const pick = chip.getAttribute('data-event-skill');
      const applyEventSkill = async (skillText) => {
        try {
          disableAllEventChips();
          const response = await apiCall('/api/character/event-skill-grant', { skill_text: skillText });
          await applyResponse(response);
          if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
            uiState.lastRoll.eventSkillApplied = response.skill || skillText;
            uiState.lastRoll.eventChoicePath = 'skill';
          }
          renderAll();
        } catch (err) {
          alert(err.message || 'Could not apply that skill.');
          enableAllEventChips();
        }
      };
      if (!interceptCascadeSkill(pick, applyEventSkill)) await applyEventSkill(pick);
    });
  });

  // Event-choice DM alternative: "Take DM+N to next Advancement roll instead."
  document.querySelectorAll('[data-event-dm]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const dm = parseInt(chip.getAttribute('data-event-dm'), 10);
      const target = chip.getAttribute('data-event-dm-target');
      try {
        disableAllEventChips();
        const response = await apiCall('/api/character/event-dm-grant', { dm, target });
        await applyResponse(response);
        if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
          uiState.lastRoll.eventDmApplied = { dm: response.dm ?? dm, target: response.target ?? target };
          uiState.lastRoll.eventChoicePath = 'dm';
        }
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not apply that DM grant.');
        enableAllEventChips();
      }
    });
  });

  // Event-choice career-transfer offer: "transfer to the Marines without a
  // Qualification roll." Sets pending_transfer_career_id on the character.
  document.querySelectorAll('[data-event-transfer]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const careerId = chip.getAttribute('data-event-transfer');
      try {
        disableAllEventChips();
        const response = await apiCall('/api/character/event-transfer-offer', { target_career_id: careerId });
        await applyResponse(response);
        if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
          uiState.lastRoll.eventTransferApplied = response.target_name || careerId;
          uiState.lastRoll.eventChoicePath = 'transfer';
        }
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not accept that transfer.');
        enableAllEventChips();
      }
    });
  });

  // Contested-roll: "Roll <Skill> 8+". On click, roll 2D + skill-level, compare
  // to target, and surface success/fail outcome. If success branch contains a
  // DM+N grant or skill grant, apply it via the existing event-dm-grant /
  // event-skill-grant endpoints.
  document.querySelectorAll('[data-contested-roll]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr || lr.type !== 'event') return;
      const parsed = parseEventContestedRoll(lr.eventText || '');
      if (!parsed) return;
      const idx = parseInt(chip.getAttribute('data-contested-roll'), 10);
      const sk = parsed.skills[idx];
      if (!sk) return;
      const mod = getSkillLevelFor(sk.name, sk.speciality);
      const roll = rollD2(mod);
      const success = roll.total >= parsed.target;
      const skillLabel = sk.speciality ? `${sk.name} (${sk.speciality})` : sk.name;
      const branchText = success ? parsed.successText : parsed.failText;

      // Apply any DM+N grants from the resolved branch via the event-dm-grant
      // endpoint (same path used for the "either skill or DM+N" picker).
      const appliedMsgs = [];
      try {
        disableAllEventChips();
        if (branchText) {
          const dmRe = /DM\s*([+-]?\d+)\s+(?:to\s+(?:a|any|your|one|the|next)\s+)?(advancement|benefit|qualification)/gi;
          let m;
          while ((m = dmRe.exec(branchText)) !== null) {
            const dm = parseInt(m[1], 10);
            const target = m[2].toLowerCase();
            try {
              const resp = await apiCall('/api/character/event-dm-grant', { dm, target });
              await applyResponse(resp);
              appliedMsgs.push(`DM${dm >= 0 ? '+' : ''}${dm} to next ${target} roll`);
            } catch (_) { /* ignore */ }
          }
        }
      } catch (_) { /* ignore */ }

      // If the success branch offers a skill pick, store it for the picker UI.
      let pendingSkillPick = null;
      if (success && branchText) {
        const sOpts = parseEventSkillOptions(branchText);
        const sWild = !sOpts ? parseEventWildcardSkill(branchText) : null;
        if ((sOpts && sOpts.length) || sWild) {
          pendingSkillPick = { options: sOpts || null, wildcardSpec: sWild || null };
        }
      }

      if (lr) {
        lr.eventContestedResolved = {
          success, dice: roll.dice, mod: roll.mod, total: roll.total,
          target: parsed.target, skillLabel, branchText, appliedMsgs,
          pendingSkillPick,
        };

        // Citizen event 8: retroactive survival DM-2 check.
        // If DM-2 to survival would have caused a failure, flag it.
        if (!success && /DM-2 to your Survival roll this term/i.test(lr.eventText || '')) {
          const term = character.current_term;
          const career = CAREERS.find(c => c.id === term?.career_id);
          const asgn = career?.assignments?.[term?.assignment_id];
          const survTarget = asgn?.survival?.target ?? 99;
          const survTotal = term?.survival_roll_total ?? null;
          if (survTotal !== null && (survTotal - 2) < survTarget) {
            lr.citizenEv8SurvivalFailed = true;
          }
        }
        if (success && /DM-2 to your Survival roll this term/i.test(lr.eventText || '')) {
          const term = character.current_term;
          const career = CAREERS.find(c => c.id === term?.career_id);
          const asgn = career?.assignments?.[term?.assignment_id];
          const survTarget = asgn?.survival?.target ?? 99;
          const survTotal = term?.survival_roll_total ?? null;
          if (survTotal !== null && (survTotal - 2) < survTarget) {
            lr.citizenEv8SurvivalFailed = true;
          }
        }

        // Scout event 2: on failure, ban Scout from future careers.
        if (!success && /may not re-enlist in the Scouts/i.test(branchText || '')) {
          try {
            const resp = await apiCall('/api/character/ban-career', { career_id: 'scout' });
            await applyResponse(resp);
            lr.scoutBanned = true;
          } catch (_) {}
        }

        // Prisoner event 7: on success, mark parole granted.
        if (success && /you leave at the end of this term/i.test(branchText || '')) {
          lr.prisonerParoleGranted = true;
        }
      }
      renderAll();
    });
  });

  // "Skip — apply manually" for contested roll.
  document.querySelectorAll('[data-contested-skip]').forEach(chip => {
    chip.addEventListener('click', () => {
      const lr = uiState.lastRoll;
      if (!lr || lr.type !== 'event') return;
      lr.eventContestedResolved = {
        success: null, dice: [], mod: 0, total: 0,
        target: 0, skillLabel: 'Skipped', branchText: 'Resolve this check manually.',
        appliedMsgs: [],
      };
      renderAll();
    });
  });

  // Skill picker after a contested roll succeeds (e.g. navy[8], army[8]).
  document.querySelectorAll('[data-contested-skill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr || !lr.eventContestedResolved) return;
      const pick = chip.getAttribute('data-contested-skill');
      const applyContestedSkill = async (skillText) => {
        try {
          chip.disabled = true;
          document.querySelectorAll('[data-contested-skill]').forEach(c => { c.disabled = true; });
          const resp = await apiCall('/api/character/event-skill-grant', { skill_text: skillText });
          await applyResponse(resp);
          lr.eventContestedResolved.skillChosen = resp.skill || skillText;
          lr.eventContestedResolved.appliedMsgs = [
            ...(lr.eventContestedResolved.appliedMsgs || []),
            `+ ${resp.skill || skillText}`,
          ];
        } catch (err) {
          alert(err.message || 'Could not apply that skill.');
          document.querySelectorAll('[data-contested-skill]').forEach(c => { c.disabled = false; });
        }
        renderAll();
      };
      if (!interceptCascadeSkill(pick, applyContestedSkill)) await applyContestedSkill(pick);
    });
  });
  // Refuse branch for noble[3] / noble[8]. On click, apply the parsed
  // consequence (SOC delta or associate gain) and resolve the contested-
  // roll widget with success=null so the post-resolution view shows only
  // the refusal outcome.
  document.querySelectorAll('[data-event-refuse]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr || lr.type !== 'event') return;
      const opt = parseEventRefuseOption(lr.eventText || '');
      if (!opt) return;
      const appliedMsgs = [];
      try {
        disableAllEventChips();
        if (opt.stat && opt.delta) {
          try {
            const resp = await apiCall('/api/character/event-stat-change', {
              stat: opt.stat, delta: opt.delta, reason: 'Refused event challenge',
            });
            await applyResponse(resp);
            const sign = opt.delta >= 0 ? '+' : '';
            appliedMsgs.push(`${opt.stat} ${sign}${opt.delta}`);
          } catch (err) { /* fall through to manual */ }
        } else if (opt.associateKind) {
          try {
            const resp = await apiCall('/api/character/associate', {
              op: 'add', kind: opt.associateKind, description: opt.consequence,
            });
            await applyResponse(resp);
            appliedMsgs.push(`Gained ${opt.associateKind.charAt(0).toUpperCase() + opt.associateKind.slice(1)}`);
          } catch (err) { /* fall through */ }
        }
      } catch (_) { /* ignore */ }
      lr.eventContestedResolved = {
        success: null, dice: [], mod: 0, total: 0,
        target: 0, skillLabel: 'Refused',
        branchText: opt.consequence,
        appliedMsgs,
      };
      renderAll();
    });
  });


  // Agent event 8: cross-career roll on Rogue or Citizen table
  ['rogue', 'citizen'].forEach(careerId => {
    const btn = document.getElementById(`btn-cross-career-${careerId}`);
    if (!btn) return;
    btn.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr) return;
      const succeeded = lr.eventContestedResolved && lr.eventContestedResolved.success;
      const tbl = succeeded ? 'event' : 'mishap';
      btn.disabled = true;
      try {
        const response = await apiCall('/api/character/cross-career-roll', { career_id: careerId, table: tbl });
        await applyResponse(response);
        lr.crossCareerResult = response;
        renderAll();
      } catch (err) {
        alert(err.message || 'Cross-career roll failed.');
        btn.disabled = false;
      }
    });
  });

  // Entertainer event 5: two-stage associate picker (type → person).
  document.querySelectorAll('[data-ent-assoc-type]').forEach(btn => {
    btn.addEventListener('click', () => {
      const lr = uiState.lastRoll;
      if (!lr) return;
      lr.entertainerAssocType = btn.getAttribute('data-ent-assoc-type');
      renderAll();
    });
  });
  document.querySelectorAll('[data-ent-assoc-person]').forEach(btn => {
    btn.addEventListener('click', () => {
      const lr = uiState.lastRoll;
      if (!lr) return;
      lr.entertainerPersonType = btn.getAttribute('data-ent-assoc-person');
      renderAll();
    });
  });
  const btnEntConfirm = document.getElementById('btn-ent-assoc-confirm');
  if (btnEntConfirm) {
    btnEntConfirm.addEventListener('click', async () => {
      const lr = uiState.lastRoll;
      if (!lr || !lr.entertainerAssocType || !lr.entertainerPersonType) return;
      const kind = lr.entertainerAssocType;
      const person = lr.entertainerPersonType;
      const desc = `${person} [Entertainer event]`;
      try {
        const resp = await apiCall('/api/character/associate', { kind, description: desc });
        await applyResponse(resp);
        lr.entertainerAssocDone = `${kind.charAt(0).toUpperCase()+kind.slice(1)}: ${desc}`;
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not add associate.');
      }
    });
  }

  // Associate outcomes — "Gain a Contact/Ally/Rival/Enemy" or Betrayal convert.
  const labelAssoc = (k) => ({contact:'Contact', ally:'Ally', rival:'Rival', enemy:'Enemy'}[k] || k);
  const recordAssocDone = (opIdx, summary) => {
    if (!uiState.lastRoll || uiState.lastRoll.type !== 'event') return;
    const arr = Array.isArray(uiState.lastRoll.associateOpsDone) ? uiState.lastRoll.associateOpsDone.slice() : [];
    while (arr.length <= opIdx) arr.push(null);
    arr[opIdx] = summary;
    uiState.lastRoll.associateOpsDone = arr;
  };
  const disableAllAssocChips = () => {
    document.querySelectorAll('[data-assoc-add],[data-assoc-convert]').forEach(c => { c.disabled = true; });
  };
  const enableAllAssocChips = () => {
    document.querySelectorAll('[data-assoc-add],[data-assoc-convert]').forEach(c => { c.disabled = false; });
  };

  document.querySelectorAll('[data-assoc-add]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const opIdx = parseInt(chip.getAttribute('data-assoc-add'), 10);
      const kind = chip.getAttribute('data-assoc-kind');
      const descEl = document.querySelector(`[data-assoc-desc="${opIdx}"]`);
      const description = (descEl?.value || '').trim();
      try {
        disableAllAssocChips();
        const response = await apiCall('/api/character/associate', {
          op: 'add', kind, description,
        });
        await applyResponse(response);
        const summary = `Gained ${labelAssoc(kind)}${description ? `: ${description}` : ''}`;
        recordAssocDone(opIdx, summary);
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not add that associate.');
        enableAllAssocChips();
      }
    });
  });

  document.querySelectorAll('[data-assoc-convert]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const opIdx = parseInt(chip.getAttribute('data-assoc-convert'), 10);
      const index = parseInt(chip.getAttribute('data-assoc-index'), 10);
      const toKind = chip.getAttribute('data-assoc-to');
      try {
        disableAllAssocChips();
        const response = await apiCall('/api/character/associate', {
          op: 'convert', index, to_kind: toKind,
        });
        await applyResponse(response);
        const conv = response.converted || {};
        const summary = `Betrayal — ${labelAssoc(conv.from_kind || '')} → ${labelAssoc(conv.to_kind || toKind)}${conv.description ? `: ${conv.description}` : ''}`;
        recordAssocDone(opIdx, summary);
        renderAll();
      } catch (err) {
        alert(err.message || 'Could not convert that associate.');
        enableAllAssocChips();
      }
    });
  });

  const btnMishap = document.getElementById('btn-mishap');
  if (btnMishap) {
    btnMishap.addEventListener('click', async () => {
      const response = await apiCall('/api/character/mishap');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'mishap',
        data: response.roll,
        mishapText: response.mishap,
        autoApplied: response.auto_applied || [],
        injuryPending: response.injury_pending || false,
        injuryTitle: response.injury_data?.title || null,
        injuryText: response.injury_data?.text || null,
        injuryRoll: response.injury_data?.roll?.total ?? null,
        frozenWatch: response.frozen_watch || false,
      };
      renderAll();
    });
  }

  const btnPostMishap = document.getElementById('btn-post-mishap');
  if (btnPostMishap) {
    btnPostMishap.addEventListener('click', async () => {
      await endTermWithAgingIntercept(true, 'mishap', { type: 'muster_out_mishap' });
    });
  }

  // Helper: call career-mishap-choice and refresh state
  async function resolveMishapChoice(choiceData) {
    const response = await apiCall('/api/character/career-mishap-choice', { choice_data: choiceData });
    await applyResponse(response);
    if (uiState.lastRoll) {
      uiState.lastRoll.autoApplied = [
        ...(uiState.lastRoll.autoApplied || []),
        ...(response.auto_applied || []),
      ];
      uiState.lastRoll.injuryPending = response.injury_pending || false;
      if (response.injury_data) {
        uiState.lastRoll.injuryTitle = response.injury_data.title;
        uiState.lastRoll.injuryText = response.injury_data.text;
        uiState.lastRoll.injuryRoll = response.injury_data?.roll?.total ?? null;
      }
      if (response.skill_check) {
        uiState.lastRoll.skillCheckResult = response.skill_check;
      }
    }
    renderAll();
  }

  // Injury severity choice buttons
  const btnSeverityResult2 = document.getElementById('btn-mishap-choice-result2');
  if (btnSeverityResult2) {
    btnSeverityResult2.addEventListener('click', () => resolveMishapChoice({ choice: 'result_2' }));
  }
  const btnSeverityRollTwice = document.getElementById('btn-mishap-choice-roll-twice');
  if (btnSeverityRollTwice) {
    btnSeverityRollTwice.addEventListener('click', () => resolveMishapChoice({ choice: 'roll_twice' }));
  }

  // Stat choice buttons
  document.querySelectorAll('[id^="btn-mishap-statchoice-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const stat = btn.id.replace('btn-mishap-statchoice-', '');
      resolveMishapChoice({ stat });
    });
  });

  // Skill choice buttons (specific options)
  document.querySelectorAll('[id^="btn-mishap-skillchoice-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const skill = btn.id.replace('btn-mishap-skillchoice-', '');
      resolveMishapChoice({ skill });
    });
  });

  // Any-skill choice chips (open picker — cascade skills go through specialty overlay first)
  document.querySelectorAll('[data-mishap-anyskill]').forEach(chip => {
    chip.addEventListener('click', async () => {
      const skill = chip.dataset.mishapAnyskill;
      if (CASCADE_SKILLS[skill]) {
        interceptCascadeSkill(skill, async (fullText) => {
          const nameOnly = fullText.replace(/\s+\d+\s*$/, '').trim();
          await resolveMishapChoice({ skill: nameOnly });
        });
      } else {
        await resolveMishapChoice({ skill });
      }
    });
  });

  // Free skill choice
  const btnFreeSkillConfirm = document.getElementById('btn-mishap-freeskill-confirm');
  if (btnFreeSkillConfirm) {
    btnFreeSkillConfirm.addEventListener('click', () => {
      const input = document.getElementById('input-mishap-freeskill');
      const skill = input ? input.value.trim() : '';
      if (!skill) { alert('Enter a skill name.'); return; }
      resolveMishapChoice({ skill });
    });
  }

  // Deal choice buttons
  const btnDealAccept = document.getElementById('btn-mishap-deal-accept');
  if (btnDealAccept) {
    btnDealAccept.addEventListener('click', () => resolveMishapChoice({ option_id: 'accept' }));
  }
  const btnDealRefuse = document.getElementById('btn-mishap-deal-refuse');
  if (btnDealRefuse) {
    btnDealRefuse.addEventListener('click', () => resolveMishapChoice({ option_id: 'refuse' }));
  }

  // Army join/cooperate buttons
  const btnArmyJoin = document.getElementById('btn-mishap-armyjoin-join');
  if (btnArmyJoin) {
    btnArmyJoin.addEventListener('click', () => resolveMishapChoice({ option_id: 'join' }));
  }
  const btnArmyCooperate = document.getElementById('btn-mishap-armyjoin-cooperate');
  if (btnArmyCooperate) {
    btnArmyCooperate.addEventListener('click', () => resolveMishapChoice({ option_id: 'cooperate' }));
  }

  // SolSec blame choice
  const btnBlamePin = document.getElementById('btn-mishap-blame-pin');
  if (btnBlamePin) btnBlamePin.addEventListener('click', () => resolveMishapChoice({ option_id: 'pin' }));
  const btnBlameFall = document.getElementById('btn-mishap-blame-fall');
  if (btnBlameFall) btnBlameFall.addEventListener('click', () => resolveMishapChoice({ option_id: 'fall' }));

  // SolSec expose choice
  const btnExposeYes = document.getElementById('btn-mishap-expose-yes');
  if (btnExposeYes) btnExposeYes.addEventListener('click', () => resolveMishapChoice({ option_id: 'expose' }));
  const btnExposeNo = document.getElementById('btn-mishap-expose-no');
  if (btnExposeNo) btnExposeNo.addEventListener('click', () => resolveMishapChoice({ option_id: 'quiet' }));

  // Party denounce choice
  const btnDenounceYes = document.getElementById('btn-mishap-denounce-yes');
  if (btnDenounceYes) btnDenounceYes.addEventListener('click', () => resolveMishapChoice({ option_id: 'denounce' }));
  const btnDenounceNo = document.getElementById('btn-mishap-denounce-no');
  if (btnDenounceNo) btnDenounceNo.addEventListener('click', () => resolveMishapChoice({ option_id: 'silent' }));

  // SolSec interrogation choice
  const btnIntSubmit = document.getElementById('btn-mishap-interrogation-submit');
  if (btnIntSubmit) btnIntSubmit.addEventListener('click', () => resolveMishapChoice({ option_id: 'submit' }));
  const btnIntRefuse = document.getElementById('btn-mishap-interrogation-refuse');
  if (btnIntRefuse) btnIntRefuse.addEventListener('click', () => resolveMishapChoice({ option_id: 'refuse' }));

  // Mishap victim buttons
  document.querySelectorAll('[id^="btn-mishap-victim-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.id === 'btn-mishap-victim-skip') {
        // No contacts/allies — clear pending
        resolveMishapChoice({ option_id: 'skip' });
        return;
      }
      const idx = parseInt(btn.getAttribute('data-assoc-idx'), 10);
      resolveMishapChoice({ associate_index: idx });
    });
  });

  // Skill check buttons
  document.querySelectorAll('[id^="btn-mishap-skillcheck-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const skillName = btn.getAttribute('data-skill');
      resolveMishapChoice({ skill_name: skillName });
    });
  });

  // Commission roll (Army / Navy / Marine only)
  const btnCommission = document.getElementById('btn-commission');
  if (btnCommission) {
    btnCommission.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/commission');
        await applyResponse(response);
        uiState.lastRoll = {
          type: 'commission',
          data: response.roll,
          succeeded: response.succeeded,
          newRank: response.new_rank,
          newRankTitle: response.new_rank_title,
          rankBonus: response.rank_bonus,
        };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  }

  const btnAdvance = document.getElementById('btn-advance');
  if (btnAdvance) {
    btnAdvance.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/advance');
        await applyResponse(response);
        const advRoll = {
          type: 'advance',
          data: response.roll,
          outcome: response.advanced ? 'pass' : 'fail',
          newRank: response.new_rank,
          newRankTitle: response.new_rank_title,
          forcedFromCareer: response.forced_from_career || false,
        };
        uiState.lastRoll = advRoll;
        uiState.lastAdvanceRoll = advRoll;
        if (response.advanced && response.advancement_skill_roll) {
          uiState.pendingAdvancementSkill = true;
        } else {
          uiState.pendingAdvancementSkill = false;
        }
        renderAll();
      } catch (e) { alert(e.message); }
    });
  }

  // Wire advancement bonus skill table buttons
  document.querySelectorAll('[data-adv-skill-table]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tableKey = btn.dataset.advSkillTable;
      try {
        const response = await apiCall('/api/character/skill-roll', { table_key: tableKey });
        await applyResponse(response);
        uiState.pendingAdvancementSkill = false;
        // Carry the gained skill onto the advance roll so the result screen can show it
        if (uiState.lastAdvanceRoll) {
          uiState.lastAdvanceRoll = {
            ...uiState.lastAdvanceRoll,
            advancementSkillGained: response.applied || response.result || '',
          };
        }
        // Restore the advance roll view so decide actions are shown
        uiState.lastRoll = uiState.lastAdvanceRoll ? { ...uiState.lastAdvanceRoll } : uiState.lastRoll;
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  // ── Aging intercept helpers ───────────────────────────────────────────
  // After every end-term call, if aging occurred (term 4+) we pause to show
  // the player the roll result before continuing to the next phase.
  async function executeNextAction(nextAction) {
    if (nextAction.type === 'next_term') {
      // Intercept for anagathics before starting the next term (every term, per user request).
      if (!uiState.anagathicsPhaseDone) {
        uiState.pendingNextTermAction = nextAction;
        uiState.agingResult = null;
        uiState.agingNextAction = null;
        // Clear active term state so renderCareerPhase() sees !term → anagathics prompt
        uiState.selectedCareer = null;
        uiState.selectedAssignment = null;
        uiState.subPhase = null;
        renderAll();
        return;
      }
      const startResp = await apiCall('/api/character/start-term', {
        career_id: nextAction.careerId,
        assignment_id: nextAction.assignmentId,
      });
      await applyResponse(startResp);
      uiState.lastRoll = null;
      uiState.subPhase = 'train';
    } else if (nextAction.type === 'muster_out') {
      uiState.subPhase = null;
      uiState.selectedCareer = null;
      uiState.selectedAssignment = null;
    } else if (nextAction.type === 'muster_out_mishap') {
      uiState.lastRoll = null;
      uiState.subPhase = null;
      uiState.selectedCareer = null;
      uiState.selectedAssignment = null;
    }
    uiState.agingResult = null;
    uiState.agingNextAction = null;
    renderAll();
  }

  async function endTermWithAgingIntercept(leaving, reason, nextAction) {
    // Each term end resets the anagathics gate for the next career-selection cycle.
    uiState.anagathicsPhaseDone = false;
    uiState.pendingNextTermAction = null;
    const endResp = await apiCall('/api/character/end-term', { leaving, reason });
    await applyResponse(endResp);
    if (endResp.aging !== null) {
      // Aging happened — show the roll before proceeding
      uiState.agingResult = endResp.aging;
      uiState.agingNextAction = nextAction;
      uiState.agingSelectedStats = [];   // reset any prior selections
      uiState.subPhase = 'aging_result';
      renderAll();
    } else {
      await executeNextAction(nextAction);
    }
  }

  // Aging stat-choice buttons (wired when aging_result sub-phase has pending_reductions)
  document.querySelectorAll('.aging-stat-btn:not([disabled])').forEach(btn => {
    btn.addEventListener('click', () => {
      const stat = btn.dataset.stat;
      const amount = parseInt(btn.dataset.amount, 10) || 1;
      const pending = uiState.agingResult?.pending_reductions || [];
      const totalRequired = pending.reduce((s, p) => s + p.count, 0);
      if (!uiState.agingSelectedStats) uiState.agingSelectedStats = [];
      if (uiState.agingSelectedStats.length < totalRequired) {
        uiState.agingSelectedStats.push({ stat, amount });
        renderStage();
      }
    });
  });

  // Clear aging selection
  const btnAgingClearSel = document.getElementById('btn-aging-clear-selection');
  if (btnAgingClearSel) {
    btnAgingClearSel.addEventListener('click', () => {
      uiState.agingSelectedStats = [];
      renderStage();
    });
  }

  // ── Anagathics one-time intro screen ─────────────────────────────────
  const btnAnaIntroYes = document.getElementById('btn-ana-intro-yes');
  if (btnAnaIntroYes) {
    btnAnaIntroYes.addEventListener('click', async () => {
      try {
        const resp = await apiCall('/api/character/anagathics/interest', { interest: 'yes' });
        await applyResponse(resp);
        renderAll();  // will now show the per-term anagathics prompt
      } catch (e) { alert(e.message); }
    });
  }

  const btnAnaIntroNo = document.getElementById('btn-ana-intro-no');
  if (btnAnaIntroNo) {
    btnAnaIntroNo.addEventListener('click', async () => {
      try {
        const resp = await apiCall('/api/character/anagathics/interest', { interest: 'no' });
        await applyResponse(resp);
        uiState.anagathicsPhaseDone = true;
        renderAll();  // will skip anagathics and show career picker
      } catch (e) { alert(e.message); }
    });
  }

  // ── Anagathics prompt (start-of-term, RAW) ───────────────────────────
  const btnAnagathicsAttempt = document.getElementById('btn-anagathics-attempt');
  if (btnAnagathicsAttempt) {
    btnAnagathicsAttempt.addEventListener('click', async () => {
      try {
        const resp = await apiCall('/api/character/anagathics/attempt', {});
        await applyResponse(resp);
        // already_active = auto-continue (no dice); otherwise first-access SOC roll
        uiState.lastRoll = resp.already_active
          ? { type: 'anagathics_continue', costThisTerm: resp.cost_this_term }
          : { type: 'anagathics_roll', data: resp.roll, succeeded: resp.succeeded,
              nat2Prison: resp.nat2_prison, costThisTerm: resp.cost_this_term };
        renderStage();
      } catch (e) { alert(e.message); }
    });
  }

  const btnAnagathicsSkip = document.getElementById('btn-anagathics-skip');
  if (btnAnagathicsSkip) {
    btnAnagathicsSkip.addEventListener('click', async () => {
      uiState.anagathicsPhaseDone = true;
      uiState.lastRoll = null;
      if (uiState.pendingNextTermAction) {
        const action = uiState.pendingNextTermAction;
        uiState.pendingNextTermAction = null;
        await executeNextAction(action);
      } else {
        renderAll(); // will now show career picker
      }
    });
  }

  const btnAnagathicsStop = document.getElementById('btn-anagathics-stop');
  if (btnAnagathicsStop) {
    btnAnagathicsStop.addEventListener('click', async () => {
      try {
        const resp = await apiCall('/api/character/anagathics/stop', {});
        await applyResponse(resp);
        uiState.lastRoll = { type: 'anagathics_stop', aging: resp.aging };
        renderStage();
      } catch (e) { alert(e.message); }
    });
  }

  const btnAnagathicsContinueSurvive = document.getElementById('btn-anagathics-continue-survive');
  if (btnAnagathicsContinueSurvive) {
    btnAnagathicsContinueSurvive.addEventListener('click', async () => {
      uiState.anagathicsPhaseDone = true;
      uiState.lastRoll = null;
      // Natural 2 forces a Prisoner career — always go to career picker regardless of pendingNextTermAction.
      if (character.forced_next_career_id) {
        uiState.pendingNextTermAction = null;
        renderAll();
        return;
      }
      if (uiState.pendingNextTermAction) {
        const action = uiState.pendingNextTermAction;
        uiState.pendingNextTermAction = null;
        await executeNextAction(action);
      } else {
        renderAll(); // will show career picker
      }
    });
  }
  // ─────────────────────────────────────────────────────────────────────

  // Aging CONTINUE button (wired when aging_result sub-phase is active)
  const btnAgingContinue = document.getElementById('btn-aging-continue');
  if (btnAgingContinue) {
    btnAgingContinue.addEventListener('click', async () => {
      const nextAction = uiState.agingNextAction;
      const pending = uiState.agingResult?.pending_reductions || [];
      const selected = uiState.agingSelectedStats || [];

      // If there are pending physical reductions the player has chosen, resolve them first
      if (pending.length > 0 && selected.length > 0) {
        try {
          const resolveResp = await apiCall('/api/character/resolve-aging', {
            reductions: selected,
          });
          await applyResponse(resolveResp);
        } catch (e) {
          alert(e.message);
          return;
        }
      }

      uiState.agingSelectedStats = [];
      await executeNextAction(nextAction);
    });
  }
  // ─────────────────────────────────────────────────────────────────────

  const btnContinue = document.getElementById('btn-continue-career');
  if (btnContinue) {
    btnContinue.addEventListener('click', async () => {
      const careerId = character.current_term?.career_id || uiState.selectedCareer;
      const assignmentId = character.current_term?.assignment_id || uiState.selectedAssignment;
      await endTermWithAgingIntercept(false, 'voluntary', { type: 'next_term', careerId, assignmentId });
    });
  }

  const btnNextTerm = document.getElementById('btn-next-term');
  if (btnNextTerm) {
    btnNextTerm.addEventListener('click', async () => {
      const careerId = character.current_term.career_id;
      const assignmentId = character.current_term.assignment_id;
      await endTermWithAgingIntercept(false, 'voluntary', { type: 'next_term', careerId, assignmentId });
    });
  }

  const btnLeaveCareer = document.getElementById('btn-leave-career');
  if (btnLeaveCareer) {
    btnLeaveCareer.addEventListener('click', async () => {
      await endTermWithAgingIntercept(true, 'voluntary', { type: 'muster_out' });
    });
  }

  // Forced-career sentence button (shown instead of muster-out when forced_next_career_id is set)
  const btnEnterForcedCareer = document.getElementById('btn-enter-forced-career');
  if (btnEnterForcedCareer) {
    btnEnterForcedCareer.addEventListener('click', async () => {
      await endTermWithAgingIntercept(true, 'conviction', { type: 'muster_out_mishap' });
    });
  }

  // Frozen Watch — stay in service, start next term of same career/assignment
  const btnFrozenWatch = document.getElementById('btn-frozen-watch-continue');
  if (btnFrozenWatch) {
    btnFrozenWatch.addEventListener('click', async () => {
      try {
        const careerId = character.current_term.career_id;
        const assignmentId = character.current_term.assignment_id;
        await endTermWithAgingIntercept(false, 'voluntary', { type: 'next_term', careerId, assignmentId });
      } catch (e) { alert(e.message); }
    });
  }

  // Injury roll (from mishap screen)
  const btnRollInjury = document.getElementById('btn-roll-injury');
  if (btnRollInjury) {
    btnRollInjury.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/injury');
        await applyResponse(response);
        uiState.lastRoll = {
          ...uiState.lastRoll,
          type: 'mishap',
          injuryTitle: response.title,
          injuryText: response.text,
          injuryPending: !!response.pending_choice,
          injuryData: response.pending_choice,
        };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  }

  // Injury stat choice buttons (career/mishap phase)
  ['STR', 'DEX', 'END'].forEach(stat => {
    const btn = document.getElementById(`btn-career-injury-stat-${stat}`);
    if (btn) btn.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/injury-choice', { chosen_stat: stat });
        await applyResponse(response);
        if (response.treatment_choice_pending) {
          // Show treatment choice screen before finalizing
          uiState.lastRoll = { ...uiState.lastRoll, injuryPending: false, treatmentPending: true };
          renderAll();
          return;
        }
        uiState.lastRoll = { ...uiState.lastRoll, injuryPending: false };
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  // Career/mishap injury treatment buttons (accept loss OR pay debt)
  wireInjuryTreatmentButtons('career-treatment', (_resp, _paid) => {
    uiState.lastRoll = { ...uiState.lastRoll, treatmentPending: false };
    renderAll();
  });
}

function renderActiveTerm() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const assignment = career.assignments[term.assignment_id];

  const banner = `
    <div class="term-banner">
      <span class="term-part"><strong>${career.name}</strong> · ${assignment.name}</span>
      <span class="term-part">TERM <strong>${term.overall_term_number}</strong> · AGE <strong>${character.age}</strong></span>
      <span class="term-part">RANK <strong>${term.rank}</strong>${term.rank_title ? ` — ${term.rank_title}` : ''}</span>
    </div>
  `;

  // Sub-phase dispatcher
  if (uiState.subPhase === 'qualify') {
    return renderQualifyResult();
  }
  if (uiState.subPhase === 'train' || uiState.subPhase === null) {
    return banner + renderSkillChoice();
  }
  if (uiState.subPhase === 'anagathics_prompt') {
    return banner + renderAnagathicsPrompt();
  }
  if (uiState.subPhase === 'survive') {
    return banner + renderSurviveStep();
  }
  if (uiState.subPhase === 'event') {
    return banner + renderEventStep();
  }
  if (uiState.subPhase === 'mishap') {
    return banner + renderMishapStep();
  }
  if (uiState.subPhase === 'advance') {
    return banner + renderAdvanceStep();
  }
  if (uiState.subPhase === 'decide') {
    return banner + renderDecideStep();
  }
  if (uiState.subPhase === 'aging_result') {
    return banner + renderAgingResult();
  }
  return banner + '<div class="stage-content"><p>Unknown sub-phase</p></div>';
}

function renderAgingResult() {
  const aging = uiState.agingResult;
  if (!aging) return '';

  const roll = aging.roll;
  const title = aging.title || 'Unknown';
  const autoEffects = aging.effects_applied || [];
  const pending = aging.pending_reductions || [];  // [{type, count, amount, options}]
  const noEffect = autoEffects.length === 0 && pending.length === 0;
  const nextAction = uiState.agingNextAction || {};

  // Color coding by severity
  const severityColor = noEffect
    ? 'var(--success, #7fd87f)'
    : (roll?.total ?? 0) >= -1
      ? 'var(--warning, #ffcc44)'
      : 'var(--danger, #ff5233)';

  // Auto-applied effects (mental stats)
  const autoHtml = autoEffects.length
    ? `<div class="aging-effects">${autoEffects.map(e => `<div class="aging-effect-chip">${escapeHTML(e)}</div>`).join('')}</div>`
    : '';

  // Build pending physical stat choice UI
  // selected = flat list of {stat, amount} the player has chosen
  const selected = uiState.agingSelectedStats || [];

  let pendingHtml = '';
  let totalRequired = 0;
  if (pending.length > 0) {
    totalRequired = pending.reduce((sum, p) => sum + p.count, 0);
    const selectedCount = selected.length;
    const remaining = totalRequired - selectedCount;

    // Figure out which stats are still selectable
    // (can't pick the same stat twice across groups unless count > 1)
    const selectedStats = selected.map(s => s.stat);
    const availableOptions = ['STR', 'DEX', 'END'].filter(s => !selectedStats.includes(s));

    // Build amount map: if multiple groups, later selections use later group's amount
    // For simplicity, use first pending group's amount for all (usually only 1 group)
    const currentGroupAmount = (() => {
      let filled = 0;
      for (const p of pending) {
        if (selectedCount < filled + p.count) return p.amount;
        filled += p.count;
      }
      return pending[pending.length - 1]?.amount || 1;
    })();

    const statsHtml = ['STR', 'DEX', 'END'].map(stat => {
      const alreadyChosen = selectedStats.includes(stat);
      const currentVal = character.characteristics?.[stat] ?? '?';
      const reducedVal = alreadyChosen ? (currentVal - (selected.find(s => s.stat === stat)?.amount ?? 1)) : null;
      const disabled = (alreadyChosen || remaining === 0) ? ' disabled' : '';
      const chosenClass = alreadyChosen ? ' chosen' : '';
      return `
        <button class="card aging-stat-btn${chosenClass}" data-stat="${stat}" data-amount="${currentGroupAmount}"${disabled}>
          <div class="card-title">${stat}</div>
          <div class="card-meta">${alreadyChosen ? `${currentVal} → ${reducedVal}` : `Current: ${currentVal}`}</div>
          <div class="card-desc">${alreadyChosen ? '✓ Selected' : `Reduce by ${currentGroupAmount}`}</div>
        </button>`;
    }).join('');

    pendingHtml = `
      <div class="event-box" style="border-color:var(--amber);margin-top:12px">
        <span class="event-label" style="color:var(--amber)">CHOOSE PHYSICAL STAT REDUCTIONS</span>
        <p class="phase-body">Select ${totalRequired} characteristic${totalRequired !== 1 ? 's' : ''} to reduce. (${selectedCount}/${totalRequired} chosen)</p>
        <div class="card-grid" style="max-width:360px">${statsHtml}</div>
        ${selected.length > 0 ? `
          <div style="margin-top:8px">
            <span class="empty">Selected: </span>
            ${selected.map(s => `<span class="skill-chip">${s.stat} −${s.amount}</span>`).join(' ')}
            <button class="btn ghost" id="btn-aging-clear-selection" style="margin-left:8px;font-size:11px">CLEAR</button>
          </div>` : ''}
      </div>`;
  }

  // All choices made (or no choices needed)
  const allChosen = pending.length === 0 || selected.length >= totalRequired;
  const continueLabel = nextAction.type === 'next_term' ? 'BEGIN NEXT TERM →' : 'CONTINUE →';
  const noEffectHtml = noEffect
    ? `<p class="phase-body" style="color:${severityColor}">No characteristics were reduced.</p>`
    : '';

  // Anagathics info for next term (reminder — actual roll is at START of next term)
  const anagathicsHtml = anagathicsBoxHTML();

  return `
    <div class="stage-content">
      <div class="phase-label">Aging Roll</div>
      <h2 class="phase-title" style="color:${severityColor}">${escapeHTML(title)}</h2>
      ${roll ? rollReadoutHTML(roll, { label: `2D${roll.modifier >= 0 ? '+' : ''}${roll.modifier ?? ''}`, showTarget: false }) : ''}
      <div class="event-box" style="border-color:${severityColor}">
        <span class="event-label" style="color:${severityColor}">AGING — Term ${character.total_terms}, Age ${character.age}</span>
        ${noEffectHtml}
        ${autoHtml}
      </div>
      ${pendingHtml}
      ${anagathicsHtml}
      <div class="phase-actions" style="margin-top:16px">
        <button class="btn primary" id="btn-aging-continue" ${allChosen ? '' : 'disabled'}>${continueLabel}</button>
      </div>
    </div>
  `;
}

function renderQualifyResult() {
  // User clicked a career card, qualification was rolled.
  const roll = uiState.lastRoll;
  const career = CAREERS.find(c => c.id === uiState.selectedCareer);

  if (roll.automatic) {
    // Auto-qualify → go straight to assignment pick
    return `
      <div class="panel-header"><span class="led"></span><span>QUALIFICATION — AUTOMATIC</span></div>
      <div class="stage-content">
        <div class="phase-label">${career.name}</div>
        <h2 class="phase-title">Welcome Aboard</h2>
        <p class="phase-subtitle">Automatic qualification. No roll required.</p>
        ${renderAssignmentPicker(career)}
      </div>
    `;
  }

  const r = roll.roll;
  if (roll.succeeded) {
    return `
      <div class="panel-header"><span class="led"></span><span>QUALIFICATION — PASS</span></div>
      <div class="stage-content">
        <div class="phase-label">${career.name}</div>
        <h2 class="phase-title">Accepted</h2>
        <div class="roll-readout">
          <span class="dice">[${r.dice.join(', ')}]</span>
          ${r.modifier !== 0 ? `<span class="eq">${r.modifier > 0 ? '+' : ''}${r.modifier}</span>` : ''}
          <span class="eq">=</span>
          <span class="total">${r.total}</span>
          <span class="eq">vs ${r.target}+</span>
          <span class="outcome pass">PASS</span>
        </div>
        ${renderAssignmentPicker(career)}
      </div>
    `;
  } else {
    return `
      <div class="panel-header"><span class="led"></span><span>QUALIFICATION — FAIL</span></div>
      <div class="stage-content">
        <div class="phase-label">${career.name}</div>
        <h2 class="phase-title">Rejected</h2>
        <div class="roll-readout">
          <span class="dice">[${r.dice.join(', ')}]</span>
          ${r.modifier !== 0 ? `<span class="eq">${r.modifier > 0 ? '+' : ''}${r.modifier}</span>` : ''}
          <span class="eq">=</span>
          <span class="total">${r.total}</span>
          <span class="eq">vs ${r.target}+</span>
          <span class="outcome fail">FAIL</span>
        </div>
        <p class="phase-body">You didn't qualify. The rules offer three options:</p>
        <ul class="phase-body" style="padding-left:20px;line-height:1.7">
          <li><strong>Accept the Draft</strong> — 1D determines which service takes you (Navy, Army, Marines, Merchant Marine, Scouts, or Agent). No choice in assignment, but you start a term immediately.</li>
          <li><strong>Become a Drifter</strong> — auto-qualifies, rough life, cheap mustering benefits.</li>
          <li><strong>Try Another Career</strong> — attempt a different qualification. Each previously failed career attempt applies DM−1 to this roll.</li>
        </ul>
        <div class="phase-actions">
          <button class="btn primary" id="btn-accept-draft">ACCEPT THE DRAFT</button>
          <button class="btn" id="btn-drifter-auto">BECOME A DRIFTER</button>
          <button class="btn" id="btn-back-careers">← TRY ANOTHER CAREER</button>
        </div>
      </div>
    `;
  }
}

function renderDraftResult() {
  const roll = uiState.lastRoll;
  const r = roll.roll;
  return `
    <div class="panel-header"><span class="led"></span><span>DRAFT — CONSCRIPTED</span></div>
    <div class="stage-content">
      <div class="phase-label">${roll.career_name}</div>
      <h2 class="phase-title">Drafted into ${roll.assignment_name}</h2>
      <div class="roll-readout">
        <span class="dice">[${r.dice.join(', ')}]</span>
        <span class="eq">=</span>
        <span class="total">${r.total}</span>
        <span class="outcome pass">DRAFT</span>
      </div>
      <p class="phase-body">The papers came through. You're now a ${roll.assignment_name} in the ${roll.career_name}. Basic training starts on arrival.</p>
      <div class="phase-actions">
        <button class="btn primary" id="btn-begin-drafted-term">BEGIN TERM →</button>
      </div>
    </div>
  `;
}

function renderAssignmentPicker(career) {
  // Home Forces training result banner (shown once after enrolling)
  let hfTrainingBanner = '';
  if (uiState.lastRoll?.type === 'home_forces_training') {
    const lr = uiState.lastRoll;
    hfTrainingBanner = `
      <div style="margin-bottom:14px;padding:12px 14px;border:1px solid var(--accent);border-radius:6px;background:rgba(0,255,170,0.04)">
        <div style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">HOME FORCES RESERVES — ENROLLED (${lr.component?.toUpperCase()})</div>
        <div style="margin-top:6px;font-size:13px;color:var(--text)">
          Training roll [1D=${lr.roll?.raw_total ?? '?'}]: <strong>${escapeHTML(lr.result || '')}</strong>
        </div>
        <div style="font-size:12px;color:var(--text-dim);margin-top:3px">
          Auto-skill: ${escapeHTML(lr.auto_skill || '')} 0
          ${lr.rank_transferred ? ` · Military rank ${lr.rank_transferred} transferred.` : ''}
        </div>
        <div class="phase-actions" style="margin-top:8px">
          <button class="btn ghost" id="btn-hf-training-dismiss" style="font-size:11px;padding:6px 12px">DISMISS →</button>
        </div>
      </div>
    `;
  }

  const isSecretAgentSelected = career.id === 'solsec' && uiState.selectedAssignment === 'secret_agent';
  const soc = character.society_id || 'third_imperium';

  // Cover career picker — only relevant for SolSec Secret Agent
  const COVER_CAREER_EXCLUDE = new Set(['solsec', 'party', 'drifter', 'prisoner']);
  const _coverSpeciesId = character.species_id || null;
  const coverCareers = CAREERS.filter(c => {
    if (COVER_CAREER_EXCLUDE.has(c.id)) return false;
    if (c.societies && c.societies.length > 0 && !c.societies.includes(soc)) return false;
    if (c.blocked_societies && c.blocked_societies.includes(soc)) return false;
    if (c.allowed_species && c.allowed_species.length > 0 && (!_coverSpeciesId || !c.allowed_species.includes(_coverSpeciesId))) return false;
    if (c.blocked_species && c.blocked_species.includes(_coverSpeciesId)) return false;
    return true;
  });

  const coverPickerHTML = isSecretAgentSelected ? `
    <div style="margin-top:20px;padding:14px;border:1px solid var(--amber-dim);border-radius:6px">
      <div style="font-size:11px;letter-spacing:0.2em;color:var(--amber-dim);margin-bottom:10px">
        SELECT COVER CAREER — Your public identity. Survival uses cover career stats DM-1; advancement uses cover career stats DM+1.
      </div>
      <div class="card-grid" style="grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px">
        ${coverCareers.map(c => `
          <button class="card${uiState.selectedCoverCareer === c.id ? ' selected' : ''}" data-cover-career="${c.id}"
            style="padding:10px 12px">
            <div class="card-title" style="font-size:12px">${c.name}</div>
          </button>
        `).join('')}
      </div>
      ${uiState.selectedCoverCareer ? `
        <p style="font-size:11px;color:var(--accent);margin-top:8px">
          ✓ Cover: <strong>${CAREERS.find(c=>c.id===uiState.selectedCoverCareer)?.name}</strong>
          — survival and advancement use this career's stats (DM-1 / DM+1).
        </p>` : `
        <p style="font-size:11px;color:var(--text-dim);margin-top:8px">Select a cover career above to continue.</p>
      `}
    </div>
  ` : '';

  const readyToStart = uiState.selectedAssignment &&
    (!isSecretAgentSelected || uiState.selectedCoverCareer);

  const cards = Object.entries(career.assignments).map(([id, a]) => `
    <button class="card ${uiState.selectedAssignment === id ? 'selected' : ''}" data-assignment="${id}">
      <div class="card-title">${a.name}</div>
      <div class="card-meta">SURV ${a.survival.characteristic} ${a.survival.target}+ · ADV ${a.advancement.characteristic} ${a.advancement.target}+</div>
      <div class="card-desc">${a.description}</div>
    </button>
  `).join('');

  // ---- Solomani parallel service panels ----
  const isSolomani = (character.society_id === 'solomani_confederation');
  const isBarredFromHF = (career.id === 'drifter')
    || (career.id === 'rogue' && uiState.selectedAssignment === 'pirate')
    || (career.id === 'solsec');
  const showHomeForces = isSolomani && !isBarredFromHF;
  const showMonitor = isSolomani && career.id !== 'solsec';

  // Determine which HF component this character would join
  const isNavalMerchant = career.id === 'merchant'
    && (uiState.selectedAssignment === 'merchant_marine' || uiState.selectedAssignment === 'free_trader');
  const hasExNavy = character.completed_careers && character.completed_careers.some(
    c => c.career_id === 'navy' || c.career_id === 'confederation_navy');
  const hfComponent = (isNavalMerchant || hasExNavy) ? 'naval' : 'groundside';
  const hfComponentLabel = hfComponent === 'naval' ? 'Naval' : 'Groundside';

  const homeForcesHTML = showHomeForces ? `
    <div style="margin-top:16px;padding:12px 14px;border:1px solid var(--border);border-radius:6px">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <div style="flex:1;min-width:200px">
          <div style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">HOME FORCES RESERVES (${hfComponentLabel})</div>
          <div style="font-size:12px;color:var(--text-dim);margin-top:3px">
            ${character.home_forces_enrolled
              ? `Enrolled · Rank ${character.home_forces_rank}`
              : 'Part-time planetary defence. Automatic enlistment — gains training skill + ' + (hfComponent === 'naval' ? 'Vacc Suit 0' : 'Gun Combat 0') + '.'}
          </div>
        </div>
        ${character.home_forces_enrolled
          ? `<button class="btn ghost" id="btn-hf-leave" style="font-size:11px;padding:6px 12px">RESIGN</button>`
          : `<button class="btn ghost" id="btn-hf-enroll" style="font-size:11px;padding:6px 12px">ENLIST (Roll Training)</button>`
        }
      </div>
      ${character.home_forces_enrolled ? `
        <p style="font-size:11px;color:var(--text-dim);margin:6px 0 0">
          Nat-2 on survival → also rolls ${hfComponent === 'naval' ? 'Confederation Navy' : 'Confederation Army'} Mishap table.
          ${character.home_forces_rank >= 3 ? 'Rank 3+ may use ' + hfComponentLabel + ' advancement.' : ''}
        </p>` : ''}
    </div>
  ` : '';

  const monitorStatusColor = character.solsec_monitor ? 'var(--amber)' : 'var(--text-dim)';
  const solsecMonitorHTML = showMonitor ? `
    <div style="margin-top:10px;padding:12px 14px;border:1px solid var(--border);border-radius:6px">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <div style="flex:1;min-width:200px">
          <div style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">
            SOLSEC MONITOR${character.solsec_monitor ? ` · RANK ${character.solsec_monitor_rank}` : ''}
          </div>
          <div style="font-size:12px;color:${monitorStatusColor};margin-top:3px">
            ${character.solsec_monitor
              ? 'Active informer — DM+1 advancement, nat-2→SolSec Mishap, nat-12→SolSec Event + Contact.'
              : 'Volunteer SolSec informer. DM+1 to all advancement rolls (not Drifter).'}
          </div>
        </div>
        ${character.solsec_monitor
          ? `<button class="btn ghost" id="btn-monitor-leave" style="font-size:11px;padding:6px 12px">CEASE MONITORING</button>`
          : `<button class="btn ghost" id="btn-monitor-join" style="font-size:11px;padding:6px 12px">BECOME MONITOR</button>`
        }
      </div>
      ${character.solsec_monitor && character.solsec_monitor_rank >= 3 ? `
        <p style="font-size:11px;color:var(--accent);margin:6px 0 0">
          Rank ${character.solsec_monitor_rank}: earns one extra Benefit roll at muster-out (own table or SolSec Benefits).
        </p>` : ''}
    </div>
  ` : '';

  return `
    ${hfTrainingBanner}
    <h3 style="margin-top:${hfTrainingBanner ? '0' : '28'}px;font-family:var(--font-mono);font-size:11px;letter-spacing:0.3em;color:var(--amber-dim);text-transform:uppercase">Choose an Assignment</h3>
    <div class="card-grid">${cards}</div>
    ${coverPickerHTML}
    ${homeForcesHTML}
    ${solsecMonitorHTML}
    <div class="phase-actions" style="margin-top:16px">
      <button class="btn primary" id="btn-start-term" ${readyToStart ? '' : 'disabled'}>
        BEGIN TERM →
      </button>
    </div>
  `;
}

function renderSkillChoice() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const tables = career.skill_tables || {};

  // Post-roll view: a skill-table roll just completed
  if (uiState.lastRoll?.type === 'skill') {
    const lr = uiState.lastRoll;
    const pendingSpec = uiState.pendingCareerSpecialty;
    const specialties = pendingSpec ? (CASCADE_SKILLS[pendingSpec.skillName] || []) : [];
    return `
      <div class="stage-content">
        <div class="phase-label">Skill Training · 1D Result</div>
        <h2 class="phase-title">${lr.tableName}</h2>
        ${rollReadoutHTML(lr.data, { label: '1D', showTarget: false })}
        <div class="event-box">
          <span class="event-label">Rolled ${lr.data?.total ?? '?'} → ${escapeHTML(lr.result || '?')}</span>
          ${pendingSpec ? `<span style="color:var(--amber-dim);font-size:11px"> — ${escapeHTML(lr.applied || '')}</span>` : escapeHTML(lr.applied || '')}
        </div>
        ${pendingSpec ? `
          <div class="event-box" style="border-color:var(--amber);margin-top:10px">
            <span class="event-label" style="color:var(--amber)">CHOOSE SPECIALTY</span>
            <p style="font-size:12px;color:var(--text-dim);margin:4px 0 8px">${escapeHTML(pendingSpec.skillName)} requires a specialty. Pick one:</p>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
              ${specialties.map(s => `<button class="btn ghost specialty-chip" data-career-specialty="${escapeHTML(s)}">${escapeHTML(s)}</button>`).join('')}
            </div>
          </div>
        ` : `
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-skill">SURVIVAL ROLL →</button>
        </div>`}
      </div>
    `;
  }

  // Basic training: auto-applied by the backend — show a summary view.
  if (term.basic_training) {
    const btSkills = uiState.basicTrainingSkills || [];
    const skillItems = btSkills.length
      ? btSkills.map(s => `<li style="font-family:var(--font-mono);font-size:12px;color:var(--amber)">${escapeHTML(s)}</li>`).join('')
      : '<li style="color:var(--muted)">Skills applied — see character sheet.</li>';
    return `
      <div class="stage-content">
        <div class="phase-label">Basic Training — Auto-Applied</div>
        <h2 class="phase-title">Basic Training</h2>
        <p class="phase-subtitle">First term in this career — all Service Skills granted at level 0 automatically.</p>
        <ul style="list-style:none;padding:0;margin:12px 0">${skillItems}</ul>
        <div class="phase-actions">
          <button class="btn primary" id="btn-basic-training-continue">CONTINUE TO SURVIVAL →</button>
        </div>
      </div>
    `;
  }

  // Which tables can this character roll on?
  const available = Object.entries(tables).filter(([key, t]) => {
    if (t.assignment_only && t.assignment_only !== term.assignment_id) return false;
    if (t.requires_commission && !term.commissioned) return false;
    return true;
  });

  if (!available.length) {
    // Career has no skill tables encoded yet (stub career)
    return `
      <div class="stage-content">
        <div class="phase-label">Skill Training</div>
        <h2 class="phase-title">No Tables Encoded</h2>
        <p class="phase-body">This career's skill tables aren't in the JSON yet. You can skip the skill roll for this term and proceed to survival. (See the README for how to complete career data from the rulebook.)</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-post-skill">SURVIVAL ROLL →</button>
        </div>
      </div>
    `;
  }

  const eduGate = character.characteristics.EDU;
  const buttons = available.map(([key, t]) => {
    const gated = t.requires_edu && eduGate < t.requires_edu;
    // Build the 1–6 preview row for this table
    const previewItems = [1,2,3,4,5,6].map(n => {
      const entry = t[String(n)];
      if (!entry) return '';
      // Highlight stat bumps (e.g. "DEX +1", "END+1") in a lighter colour
      const isStatBump = /^(STR|DEX|END|INT|EDU|SOC|PSI)\s*[+-]\d+$/i.test(String(entry).trim());
      return `<span class="stable-preview-cell ${isStatBump ? 'is-stat' : ''}">`
           + `<span class="stable-preview-n">${n}</span>`
           + `<span class="stable-preview-v">${escapeHTML(String(entry))}</span>`
           + `</span>`;
    }).join('');
    return `
      <button class="btn skill-table-btn ${gated ? 'ghost' : ''}" data-skill-table="${key}" ${gated ? 'disabled' : ''}>
        <span class="stable-name">${t.name || key}${t.requires_edu ? ` <span class="stable-req">(EDU ${t.requires_edu}+)</span>` : ''}</span>
        ${previewItems ? `<span class="stable-preview">${previewItems}</span>` : ''}
      </button>
    `;
  }).join('');

  const acr = uiState.academyCommissionRoll;
  const commRollHTML = acr ? (() => {
    const outcome = acr.succeeded ? 'Commissioned at Rank 1' : 'Not commissioned — starting as enlisted';
    uiState.academyCommissionRoll = null; // show once
    return `
      <div class="dm-applied-box" style="margin-bottom:12px">
        <span class="event-label">Academy Commission Roll</span>
        <div class="dm-chip applied">2D [${(acr.dice || []).join(' · ')}] +${acr.modifier ?? acr.dm ?? 0} = ${acr.total} vs ${acr.target}+ — ${escapeHTML(outcome)}</div>
      </div>
    `;
  })() : '';

  return `
    <div class="stage-content">
      <div class="phase-label">Skill Training · 1D Roll</div>
      <h2 class="phase-title">Skills and Training</h2>
      <p class="phase-subtitle">Pick one skill table and roll 1D on it.</p>
      ${commRollHTML}
      <div class="phase-actions" style="flex-direction:column;align-items:stretch;gap:8px">
        ${buttons}
      </div>
    </div>
  `;
}

function renderAnagathicsIntroScreen() {
  const soc = character.characteristics?.SOC ?? 0;
  const dm = charDM(soc);
  return `
    <div class="stage-content">
      <div class="phase-label">Anagathics · One-Time Setup</div>
      <h2 class="phase-title">Interested in Anagathics?</h2>
      <p class="phase-body">
        Anagathic drugs halt aging — but they're expensive, risky, and hard to obtain.
        Each term you can roll <strong>SOC 10+</strong> to secure a supply.
      </p>
      <ul class="phase-body" style="margin:8px 0 12px 1.2em;color:var(--text-dim);font-size:13px">
        <li>🎲 <strong>One-time roll:</strong> Roll SOC 10+ once to establish supply. No re-roll needed after that.</li>
        <li>✓ <strong>Success:</strong> Supply established — aging roll gets +terms DM each term going forward.</li>
        <li>✗ <strong>Fail:</strong> No supply this term — try again next term.</li>
        <li>⚠ <strong>Natural 2:</strong> Must take Prisoner career immediately.</li>
        <li>⚠ <strong>Active penalty:</strong> Two survival checks per term; either failing = Mishap.</li>
        <li>💰 <strong>Cost:</strong> 1D × Cr25,000 per term added to medical debt (paid at muster-out).</li>
        <li>🔒 <strong>Start early:</strong> The earlier you begin, the bigger the aging roll bonus.</li>
      </ul>
      <p class="phase-body">Your SOC is <strong>${soc}</strong> (DM ${formatDM(dm)}), need 10+ on 2D.</p>
      <p class="phase-body" style="color:var(--text-dim);font-size:12px">
        This choice is saved but can be changed by restarting your character.
      </p>
      <div class="phase-actions" style="flex-direction:column;align-items:stretch;gap:10px;margin-top:16px">
        <button class="btn primary" id="btn-ana-intro-yes">
          SHOW ANAGATHICS PROMPT EACH TERM →
        </button>
        <button class="btn ghost" id="btn-ana-intro-no">
          NOT INTERESTED — SKIP FOREVER
        </button>
      </div>
    </div>
  `;
}

function renderAnagathicsPrompt() {
  const lr = uiState.lastRoll;
  const soc = character.characteristics?.SOC ?? 0;
  const dm = charDM(soc);
  const already = character.anagathics_active;
  const termsUsed = character.anagathics_terms_used ?? 0;

  // Post-roll view — show result of the initial SOC 10+ access attempt
  if (lr?.type === 'anagathics_roll') {
    const nat2 = lr.nat2Prison;
    const pass = lr.succeeded;
    const cost = lr.costThisTerm;
    return `
      <div class="stage-content">
        <div class="phase-label">Anagathics — First Access Roll (SOC 10+)</div>
        <h2 class="phase-title" style="color:${nat2 ? 'var(--danger)' : pass ? 'var(--success,#7fd87f)' : 'var(--text-dim)'}">
          ${nat2 ? 'NATURAL 2 — PRISONER' : pass ? 'Supply Established' : 'Unable to Obtain'}
        </h2>
        ${lr.data ? rollReadoutHTML(lr.data, { label: `SOC 10+ (your DM ${formatDM(dm)})` }) : ''}
        ${nat2 ? `
          <div class="event-box" style="border-color:var(--danger);margin-top:12px">
            <span class="event-label" style="color:var(--danger)">FORCED INTO PRISONER CAREER</span>
            A natural 2 on the access roll means you must take the Prisoner career this term.
          </div>` : pass ? `
          <div class="event-box" style="border-color:var(--success,#7fd87f);margin-top:12px">
            <span class="event-label" style="color:var(--success,#7fd87f)">ANAGATHICS ACTIVE</span>
            Supply established — no re-roll needed in future terms.
            Cost Cr${cost.toLocaleString()} added to medical debt (paid at muster-out).
            <br><strong>Penalty this term:</strong> Two survival checks — either failing = Mishap.
          </div>` : `
          <div class="event-box" style="margin-top:12px">
            <span class="event-label">SUPPLY UNAVAILABLE</span>
            Unable to establish a supply this term. You may try again next term.
          </div>`}
        <div class="phase-actions" style="margin-top:16px">
          <button class="btn primary" id="btn-anagathics-continue-survive">
            ${nat2 ? 'PROCEED TO PRISONER CAREER →' : 'CONTINUE →'}
          </button>
        </div>
      </div>
    `;
  }

  // Post-auto-continue view — already active, cost added, no dice rolled
  if (lr?.type === 'anagathics_continue') {
    const cost = lr.costThisTerm;
    return `
      <div class="stage-content">
        <div class="phase-label">Anagathics — Continuing</div>
        <h2 class="phase-title" style="color:var(--success,#7fd87f)">Treatment Continues</h2>
        <div class="event-box" style="border-color:var(--success,#7fd87f);margin-top:12px">
          <span class="event-label" style="color:var(--success,#7fd87f)">SUPPLY ON HAND</span>
          Term ${termsUsed} on anagathics. Aging roll bonus: +${termsUsed} DM.
          <br>Cr${cost.toLocaleString()} (1D=${cost/25000}×Cr25,000) added to medical debt.
          <br><strong>Penalty this term:</strong> Two survival checks — either failing = Mishap.
        </div>
        <div class="phase-actions" style="margin-top:16px">
          <button class="btn primary" id="btn-anagathics-continue-survive">CONTINUE →</button>
        </div>
      </div>
    `;
  }

  // Post-stop view — show aging result from stopping
  if (lr?.type === 'anagathics_stop') {
    const aging = lr.aging;
    const roll = aging?.roll;
    const title = aging?.title || 'No Effect';
    const effects = aging?.effects_applied || [];
    const pending = aging?.pending_reductions || [];
    return `
      <div class="stage-content">
        <div class="phase-label">Anagathics Stopped</div>
        <h2 class="phase-title" style="color:var(--danger)">Withdrawal Aging</h2>
        <p class="phase-body">Stopping anagathics immediately triggers an aging roll as the body begins to age again.</p>
        ${roll ? rollReadoutHTML(roll, { label: `2D${roll.modifier >= 0 ? '+' : ''}${roll.modifier ?? ''}`, showTarget: false }) : ''}
        <div class="event-box" style="border-color:var(--danger);margin-top:12px">
          <span class="event-label" style="color:var(--danger)">AGING — ${escapeHTML(title)}</span>
          ${effects.length ? effects.map(e => `<div class="aging-effect-chip">${escapeHTML(e)}</div>`).join('') : ''}
          ${pending.length ? `<p style="color:var(--amber)">Additional physical stat reductions required — proceed to survival then apply them.</p>` : ''}
        </div>
        <div class="phase-actions" style="margin-top:16px">
          <button class="btn primary" id="btn-anagathics-continue-survive">CONTINUE →</button>
        </div>
      </div>
    `;
  }

  // ── Default prompt view ────────────────────────────────────────────────────
  // Already active: no roll needed — offer to continue (auto) or stop
  if (already) {
    return `
      <div class="stage-content">
        <div class="phase-label">Before Career Selection · Term ${character.total_terms + 1}</div>
        <h2 class="phase-title">Anagathics: Continue or Stop?</h2>
        <div class="event-box" style="border-color:var(--success,#7fd87f);margin-top:12px">
          <span class="event-label" style="color:var(--success,#7fd87f)">SUPPLY ESTABLISHED</span>
          ${termsUsed} term${termsUsed !== 1 ? 's' : ''} completed on anagathics.
          Continuing gives aging roll bonus +${termsUsed + 1} DM this term.
          <br>Cost: 1D × Cr25,000 added to medical debt. Two survival checks required.
        </div>
        <p class="phase-body" style="margin-top:12px">No SOC roll needed — your supply chain is established. Stopping triggers an immediate aging roll.</p>
        <div class="phase-actions" style="margin-top:12px">
          <button class="btn primary" id="btn-anagathics-attempt">CONTINUE ANAGATHICS →</button>
          <button class="btn danger" id="btn-anagathics-stop">STOP (aging roll now)</button>
        </div>
      </div>
    `;
  }

  // Not yet active: offer the initial SOC 10+ roll
  return `
    <div class="stage-content">
      <div class="phase-label">Before Career Selection · Term ${character.total_terms + 1}</div>
      <h2 class="phase-title">Obtain Anagathics?</h2>
      <p class="phase-body">Roll SOC 10+ to establish a supply of anagathic drugs. You only roll once — if successful, supply continues automatically in future terms.</p>
      <ul class="phase-body" style="margin:8px 0 12px 1.2em;color:var(--text-dim);font-size:13px">
        <li>✓ <strong>Success:</strong> Supply established. Aging roll gets +terms DM each term.</li>
        <li>✗ <strong>Fail:</strong> No supply this term — try again next term.</li>
        <li>⚠ <strong>Natural 2:</strong> Must take Prisoner career immediately.</li>
        <li>⚠ <strong>Active penalty:</strong> Two survival checks per term; either failing = Mishap.</li>
        <li>💰 <strong>Cost:</strong> 1D × Cr25,000 per term added to medical debt (paid at muster-out).</li>
      </ul>
      <p class="phase-body">Your SOC: <strong>${soc}</strong> (DM ${formatDM(dm)}), need 10+ on 2D.</p>
      <div class="phase-actions">
        <button class="btn primary" id="btn-anagathics-attempt">ROLL SOC 10+ FOR ANAGATHICS</button>
        <button class="btn ghost" id="btn-anagathics-skip">DECLINE →</button>
      </div>
    </div>
  `;
}

function renderSurviveStep() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const assignment = career.assignments[term.assignment_id];
  const s = assignment.survival;
  const dm = charDM(character.characteristics[s.characteristic]);

  // Post-roll view: show dice + outcome
  if (uiState.lastRoll?.type === 'survive') {
    const lr = uiState.lastRoll;
    const survived = lr.outcome === 'pass';

    // Build parallel service event notices
    const buildParallelNotice = (pe) => {
      if (!pe) return '';
      const items = Array.isArray(pe) ? pe : [pe];
      return items.map(p => {
        if (p.type === 'monitor_mishap') {
          return `<div class="event-box" style="border-color:var(--danger);margin-top:10px">
            <span class="event-label" style="color:var(--danger)">SolSec Monitor — Mishap [1D=${p.roll?.raw_total}]</span>
            ${escapeHTML(p.text)}
          </div>`;
        }
        if (p.type === 'monitor_event') {
          return `<div class="event-box" style="border-color:var(--accent);margin-top:10px">
            <span class="event-label" style="color:var(--accent)">SolSec Monitor — Event [2D=${p.roll?.raw_total}] + SolSec Contact gained</span>
            ${escapeHTML(p.text)}
          </div>`;
        }
        if (p.type === 'home_forces_mishap') {
          return `<div class="event-box" style="border-color:var(--amber);margin-top:10px">
            <span class="event-label" style="color:var(--amber)">Home Forces Reserves (${p.component}) — Mishap [1D=${p.roll?.raw_total}]</span>
            ${escapeHTML(p.text)}
          </div>`;
        }
        return '';
      }).join('');
    };

    const parallelNotice = buildParallelNotice(lr.parallel_event);

    // Anagathics second roll notice (if active)
    const ana2 = lr.anagathics_second_roll;
    const ana2HTML = ana2 ? `
      <div class="event-box" style="border-color:${ana2.succeeded ? 'var(--success,#7fd87f)' : 'var(--danger)'};margin-top:10px">
        <span class="event-label" style="color:${ana2.succeeded ? 'var(--success,#7fd87f)' : 'var(--danger)'}">
          ANAGATHICS — Second Survival Check [2D${ana2.modifier >= 0 ? '+' : ''}${ana2.modifier}=${ana2.total}]
        </span>
        ${ana2.succeeded ? 'Passed — anagathics treatment stable.' : 'FAILED — the drugs disrupted your survival. Career mishap.'}
      </div>` : '';

    return `
      <div class="stage-content">
        <div class="phase-label">Survival — ${survived ? 'Pass' : 'Fail'}</div>
        <h2 class="phase-title">${survived ? 'You Survived' : 'Career Mishap'}</h2>
        ${rollReadoutHTML(lr.data, { label: `${s.characteristic} ${s.target}+` })}
        ${ana2HTML}
        ${parallelNotice}
        <p class="phase-body">${survived
          ? 'Your term continues. Roll the Event table to see what the last four years brought.'
          : 'Your career is over. Roll on the Mishap table to see how it ended.'}</p>
        <div class="phase-actions">
          <button class="btn ${survived ? 'primary' : 'danger'}" id="btn-post-survive">
            ${survived ? 'ROLL EVENT →' : 'ROLL MISHAP →'}
          </button>
        </div>
      </div>
    `;
  }

  return `
    <div class="stage-content">
      <div class="phase-label">Will You Survive?</div>
      <h2 class="phase-title">Survival Roll</h2>
      <p class="phase-subtitle">${s.characteristic} ${s.target}+ (your DM is ${formatDM(dm)})</p>

      <p class="phase-body">Fail this roll and you suffer a career-ending mishap. Welcome to Traveller.</p>

      <div class="phase-actions">
        <button class="btn primary" id="btn-survive">ROLL 2D FOR SURVIVAL</button>
      </div>
    </div>
  `;
}

function parseEventSkillOptions(text) {
  // Find skill-grant patterns in event text. Returns an array of trimmed option
  // strings, or null if no such pattern is present. Handles:
  //   - "Gain one of X, Y, Z or W"
  //   - "Gain any one of ..."
  //   - "Either gain one level of X, Y or Z, or DM+4..."
  //   - "Gain one level of X, Y or Z"
  //   - "Gain one level of X" (single skill — still returned as an array)
  //   - "Increase X by one level" (single skill)
  if (!text) return null;

  const splitToParts = (raw) => {
    // Stop the skill-list at trailing continuations like ", as well as ..."
    // or ", and gain an Ally" so the last option isn't absorbed.
    let trimmed = raw.replace(/\s*,?\s*(?:as\s+well\s+as|and\s+(?:a|an|one|gain|then)|plus|by\s+\d+)\b.*$/i, '').trim();
    trimmed = trimmed.replace(/\s*by\s+(?:one|a|\d+)\s+level\s*$/i, '').trim();
    const lastOr = trimmed.toLowerCase().lastIndexOf(' or ');
    let parts;
    if (lastOr >= 0) {
      const head = trimmed.slice(0, lastOr);
      const tail = trimmed.slice(lastOr + 4);
      parts = head.split(',').map(s => s.trim()).filter(Boolean);
      parts.push(tail.trim());
    } else {
      parts = trimmed.split(',').map(s => s.trim()).filter(Boolean);
    }
    // Skill-name sanity: letters/spaces/parens/digits, under 40 chars.
    return parts.filter(p => /^[A-Za-z][A-Za-z0-9 ()\-/]*\d*\s*$/.test(p) && p.length < 40);
  };

  // Open-ended "any skill" grants are handled by parseEventWildcardSkill —
  // which returns a dynamic list based on character / career. Return null
  // here so the caller knows to try the wildcard parser instead.
  if (/any\s+(?:one\s+)?skill\s+you\s+already\s+have/i.test(text)
      || /any\s+skill\s+of\s+your\s+choice/i.test(text)
      || /gain\s+(?:one\s+level\s+(?:in|of)\s+)?any\s+(?:skill|service\s+skill)/i.test(text)
      || /any\s+(?:one\s+)?skill\s+from\s+the\s+(?:service|officer|advanced\s+education)/i.test(text)
      || /any\s+science\s+specialty/i.test(text)) {
    return null;
  }

  // Pattern 1: "Gain one of X, Y or Z" / "Gain any one of ..."
  let m = text.match(/Gain\s+(?:any\s+)?one\s+of\s+([^.]+?)(?:\.|$)/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 2) return parts;
  }

  // Pattern 2: "Either gain one level of X, Y or Z, or DM+N..."
  //           "Either gain a level of X or ..."  (comma before "or DM" is optional)
  m = text.match(/Either\s+gain\s+(?:one|a|\d+)\s+level\s+(?:of|in)\s+([^.]+?)(?:,?\s*or\s+DM|\.|$)/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 1) return parts;
  }

  // Pattern 3: "Gain one level of X, Y or Z" (without "Either")
  m = text.match(/Gain\s+(?:one|a|\d+)\s+level\s+(?:of|in)\s+([^.]+?)(?:,\s*or\s+DM|\.|$)/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 1) return parts;
  }

  // Pattern 4: "Increase X by one level" (single skill)
  m = text.match(/Increase\s+([A-Za-z][A-Za-z0-9 ()\-/]{0,35})\s+by\s+(?:one|a|\d+)\s+level/i);
  if (m) {
    const skill = m[1].trim();
    if (skill) return [skill];
  }

  // Pattern 4b: "increase one of X, Y or Z by 1" (drifter[5])
  m = text.match(/increase\s+one\s+of\s+([^.]+?)\s+by\s+(?:one|a|\d+)(?:\s+level)?\b/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 2) return parts;
  }

  // Pattern 4c: "pick up X 1, Y 1, or Z 1" (prisoner[5])
  m = text.match(/pick\s+up\s+([^.]+?)(?:\.|$)/i);
  if (m) {
    // Strip trailing level digits ("Streetwise 1" → "Streetwise")
    const cleaned = m[1].trim().replace(/\s+\d+\b/g, '');
    const parts = splitToParts(cleaned);
    if (parts.length >= 1) return parts;
  }

  // Pattern 5: "Gain Vacc Suit 1 or Athletics (dexterity) 1"
  // "Gain X <N> or Y <N> [or Z <N>]" — skill name(s) with levels, no "one of"
  // preamble. Splits on " or " / ",", keeps the trailing digit in each part.
  m = text.match(/Gain\s+([A-Z][A-Za-z ()\-/]+?\s+\d(?:\s*(?:,|or)\s+[A-Z][A-Za-z ()\-/]+?\s+\d)+)(?:\.|$)/);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 2) return parts;
  }

  // Pattern 5b: "Gain X N or take DM+N..." — single named skill followed by
  // "or take DM" (Solomani career wording, e.g. confederation_navy event 11).
  m = text.match(/Gain\s+([A-Z][A-Za-z0-9 ()\-/]+?\s+\d)\s+or\s+take\s+DM/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 1) return parts;
  }

  return null;
}

// Curated Traveller skill catalog for "any skill of your choice" pickers.
// Kept short enough to fit a chip grid but covers every core-rulebook skill.
const ALL_TRAVELLER_SKILLS = [
  'Admin', 'Advocate', 'Animals', 'Art', 'Astrogation', 'Athletics',
  'Battle Dress', 'Broker', 'Carouse', 'Deception', 'Diplomat', 'Drive',
  'Electronics', 'Engineer', 'Explosives', 'Flyer', 'Gambler', 'Gun Combat',
  'Gunner', 'Heavy Weapons', 'Investigate', 'Jack-of-all-Trades', 'Language',
  'Leadership', 'Mechanic', 'Medic', 'Melee', 'Navigation', 'Persuade',
  'Pilot', 'Profession', 'Recon', 'Science', 'Seafarer', 'Stealth',
  'Steward', 'Streetwise', 'Survival', 'Tactics', 'Vacc Suit',
];

function parseEventWildcardSkill(text) {
  // Detect open-ended skill grants. Returns one of:
  //   { type: 'already-have' }  — "any skill you already have"
  //   { type: 'free' }          — "any skill of your choice"
  //   { type: 'service' }       — "any Service Skill (of your choice)"
  //   { type: 'service-or-advanced' } — "any skill from the Service or Advanced Education tables"
  //   { type: 'officer-or-advanced' } — "from the Officer or Advanced Education tables"
  //   { type: 'science' }       — "any Science specialty"
  // or null.
  if (!text) return null;
  if (/any\s+(?:one\s+)?skill\s+you\s+already\s+have/i.test(text)) {
    return { type: 'already-have' };
  }
  if (/any\s+science\s+specialty/i.test(text)) {
    return { type: 'science' };
  }
  if (/any\s+(?:one\s+)?skill\s+from\s+the\s+officer\s+or\s+advanced\s+education/i.test(text)) {
    return { type: 'officer-or-advanced' };
  }
  if (/any\s+(?:one\s+)?skill\s+from\s+the\s+service\s+or\s+advanced\s+education/i.test(text)
      || /any\s+(?:one\s+)?skill\s+listed\s+on\s+the\s+service\s+or\s+advanced\s+education/i.test(text)) {
    return { type: 'service-or-advanced' };
  }
  if (/any\s+service\s+skill/i.test(text)) {
    return { type: 'service' };
  }
  if (/any\s+skill\s+of\s+your\s+choice/i.test(text)) {
    return { type: 'free' };
  }
  return null;
}

// Career-transfer offers, e.g. army[10] "transfer to the Marines (without a
// Qualification roll)". Returns { career_id: '...', career_name: '...' } or
// null. Maps mentioned career names to the JSON keys used by the backend.
function parseEventTransferOffer(text) {
  if (!text) return null;
  // Generic open transfer: "transfer to any other [non-military] career"
  if (/transfer\s+to\s+any\s+other\s+(?:non-military\s+)?career/i.test(text)) {
    const nonMilitary = /non-military/i.test(text);
    return { career_id: 'any', career_name: 'any career', nonMilitary };
  }
  // Named career transfer: "transfer to the Marines" / "transfer to the Army"
  const m = /transfer\s+to\s+(?:the\s+)?([A-Z][A-Za-z]+)/.exec(text);
  if (!m) return null;
  const name = m[1];
  const map = {
    Army: 'army',
    Marines: 'marine',
    Marine: 'marine',
    Navy: 'navy',
    Scouts: 'scout',
    Scout: 'scout',
    Agents: 'agent',
    Agent: 'agent',
    Nobility: 'noble',
    Noble: 'noble',
  };
  const careerId = map[name];
  if (!careerId) return null;
  return { career_id: careerId, career_name: name };
}

// Contested-roll parser. Detects "Roll <Skill> N+" patterns and returns
// { skills: [{name, parenthetical}], target: 8, successText, failText } or null.
// Handles: "Roll Art 8+ or Persuade 8+", "Roll SOC 8+", "Roll Tactics (naval) 8+",
// "Roll Stealth 8+ or Deception 8+; on success, ...", "If you succeed ... If you fail ..."

// Parse "If you refuse, <consequence>." branches (noble[3] duel, noble[8]
// conspiracy). Returns { consequence, stat, delta, associateKind } or null.
// We only attempt mechanics for SOC deltas and associate gains — anything
// else is surfaced as text-only for manual resolution.
function parseEventRefuseOption(text) {
  if (!text) return null;
  const m = text.match(/If you refuse,\s+([^.]+?)\./i);
  if (!m) return null;
  const consequence = m[1].trim();
  const out = { consequence, stat: null, delta: 0, associateKind: null };
  // "reduce your SOC by 1" / "reduce SOC by 2" / "lose 1 SOC"
  const statRe = /(?:reduce|lose)\s+(?:your\s+)?(\d+)?\s*(STR|DEX|END|INT|EDU|SOC)(?:\s+by\s+(\d+))?/i;
  const sm = consequence.match(statRe);
  if (sm) {
    const stat = sm[2].toUpperCase();
    const amount = parseInt(sm[3] || sm[1] || '1', 10);
    out.stat = stat;
    out.delta = -Math.abs(amount);
    return out;
  }
  // "gain the conspiracy as an Enemy" / "gain an Enemy" / "gain a Rival"
  const am = consequence.match(/gain\s+(?:the\s+\w+\s+as\s+)?(?:a|an|one)\s+(?:new\s+|another\s+)?(contact|ally|rival|enemy)/i);
  if (am) {
    out.associateKind = am[1].toLowerCase();
    return out;
  }
  // Manual fallback — still return the consequence text so UI can show it.
  return out;
}

function parseEventContestedRoll(text) {
  if (!text) return null;
  // Patterns handled:
  //   "Roll Art 8+ or Persuade 8+"  (target repeated per skill)
  //   "Roll Art or Persuade 8+"     (single target at end)
  //   "Roll Tactics (naval) 8+"     (speciality in parens)
  //   "Roll INT 8+"                 (characteristic check)
  const startIdx = text.search(/\bRoll\s+[A-Z]/);
  if (startIdx < 0) return null;
  let target = null;
  const skills = [];
  let scanEnd = startIdx;
  // Scan every "<Skill> N+" and "or <Skill> N+" at the start.
  // Allow optional second capitalized word to catch multi-word skills
  // like "Gun Combat", "Heavy Weapons", "Vacc Suit".
  const chunkRe = /(?:Roll\s+|\s+or\s+|\s+and\s+)([A-Z][A-Za-z]+(?:\s+[A-Z][a-z]+)?)(?:\s*\(([a-z]+)\))?(?:\s+(\d+)\s*\+)?/gy;
  chunkRe.lastIndex = startIdx;
  let mm;
  while ((mm = chunkRe.exec(text)) !== null) {
    if (mm[3]) target = parseInt(mm[3], 10);
    skills.push({ name: mm[1], speciality: mm[2] || null });
    scanEnd = chunkRe.lastIndex;
  }
  if (!skills.length || target == null) return null;
  // Slice off the roll prefix and find success/failure branches.
  const rest = text.slice(scanEnd);
  // Split into success and fail branches using positional ordering so
  // either branch can appear first.
  let successText = rest;
  let failText = '';
  const successMarkRe = /(?:^|[;.,\s])\s*(?:on success|if you succeed)\s*[,.]?\s*/i;
  const failMarkRe = /(?:^|[;.,\s])\s*(?:on failure|on failing|if you fail)\s*[,.]?\s*/i;
  const sMatch = successMarkRe.exec(rest);
  const fMatch = failMarkRe.exec(rest);
  const markers = [];
  if (sMatch) markers.push({ kind: 'success', start: sMatch.index, textStart: sMatch.index + sMatch[0].length });
  if (fMatch) markers.push({ kind: 'fail', start: fMatch.index, textStart: fMatch.index + fMatch[0].length });
  markers.sort((a, b) => a.start - b.start);
  if (markers.length) {
    for (let i = 0; i < markers.length; i++) {
      const ev = markers[i];
      const end = i + 1 < markers.length ? markers[i + 1].start : rest.length;
      const chunk = rest.slice(ev.textStart, end).trim();
      if (ev.kind === 'success') successText = chunk;
      else failText = chunk;
    }
    if (!sMatch) successText = '';
  }
  return { skills, target, successText: successText.replace(/^[;.,\s]+/, ''), failText };
}

// Get character's level for a named skill (returns -3 if untrained, matching
// Traveller's untrained penalty). Pass lower-cased skill name, optional speciality.
function getSkillLevelFor(skillName, speciality) {
  const skills = (character && character.skills) || [];
  const lname = (skillName || '').toLowerCase();
  const lspec = speciality ? speciality.toLowerCase() : null;
  for (const s of skills) {
    if (s.name.toLowerCase() !== lname) continue;
    if (lspec && s.speciality && s.speciality.toLowerCase() === lspec) return s.level;
    if (!lspec) return Math.max(s.level || 0, 0);
  }
  // Check if it's a characteristic name (STR/DEX/etc.) — use the stat DM.
  const CHAR_KEYS = ['STR','DEX','END','INT','EDU','SOC'];
  if (CHAR_KEYS.includes(skillName.toUpperCase())) {
    const stat = character?.characteristics?.[skillName.toUpperCase()] ?? 7;
    return charDM(stat);
  }
  return -3; // untrained
}

// Roll 2D + mods and return {total, dice:[a,b], mod}.
function rollD2(mod) {
  const a = 1 + Math.floor(Math.random() * 6);
  const b = 1 + Math.floor(Math.random() * 6);
  return { dice: [a, b], mod: mod || 0, total: a + b + (mod || 0) };
}

function getCharacterSkillNames() {
  // Flat list of the character's current skills as display strings.
  // Skills with a speciality → "Name (speciality)". Plain skills → bare name.
  if (!character || !Array.isArray(character.skills)) return [];
  const out = [];
  const seen = new Set();
  for (const s of character.skills) {
    if (!s || !s.name) continue;
    const display = s.speciality ? `${s.name} (${s.speciality})` : s.name;
    if (!seen.has(display)) { seen.add(display); out.push(display); }
  }
  return out.sort();
}

function getCareerTableSkills(careerKey, tableNames) {
  // Read skill entries from a career's skill_tables and return a dedup'd list.
  // careerKey: 'navy', 'marine', etc. tableNames: ['service_skills', ...].
  const careerData = CAREER_DATA[careerKey] || null;
  const tables = careerData && careerData.skill_tables;
  if (!tables) return [];
  const out = [];
  const seen = new Set();
  for (const t of tableNames) {
    const table = tables[t];
    if (!table) continue;
    for (const k of ['1', '2', '3', '4', '5', '6']) {
      const v = table[k];
      if (v && typeof v === 'string' && !seen.has(v)) {
        seen.add(v);
        out.push(v);
      }
    }
  }
  return out;
}

function resolveWildcardSkillOptions(wildcard, careerKey) {
  // Turn a wildcard descriptor into a concrete chip list.
  if (!wildcard) return null;
  switch (wildcard.type) {
    case 'already-have':
      return getCharacterSkillNames();
    case 'service':
      return getCareerTableSkills(careerKey, ['service_skills']);
    case 'service-or-advanced':
      return getCareerTableSkills(careerKey, ['service_skills', 'advanced_education']);
    case 'officer-or-advanced':
      return getCareerTableSkills(careerKey, ['officer', 'advanced_education']);
    case 'science':
      return ['Science (archaic)', 'Science (biology)', 'Science (chemistry)',
              'Science (cosmology)', 'Science (cybernetics)', 'Science (economics)',
              'Science (genetics)', 'Science (history)', 'Science (linguistics)',
              'Science (philosophy)', 'Science (physics)', 'Science (planetology)',
              'Science (psionicology)', 'Science (psychology)', 'Science (robotics)',
              'Science (sophontology)', 'Science (xenology)'];
    case 'free':
      return ALL_TRAVELLER_SKILLS.slice();
    default:
      return null;
  }
}

function parseEventDmAlternative(text) {
  // Detect "or DM+N to/on your next/an Advancement roll" as an alternative reward.
  // Also handles "or take DM+N ..." (Solomani career wording).
  // Returns { dm: 4, target: 'advancement' } or null.
  if (!text) return null;
  const m = text.match(/or\s+(?:take\s+)?DM\s*([+-]?\d+)\s+(?:to|on)\s+(?:(?:your\s+)?next\s+|an?\s+)(Advancement|Qualification|Survival|Promotion)\s+roll/i);
  if (!m) return null;
  return { dm: parseInt(m[1], 10), target: m[2].toLowerCase() };
}

function rollAssocQuantity(expr) {
  // Resolve a Traveller-style dice expression to a count. D3 = 1-3, D6 = 1-6,
  // "1D" / "2D" = 1-6 / 2-12 (implicit d6), "NDN" = N dice of given sides,
  // bare integer = literal count.
  const e = String(expr || '').toUpperCase().trim();
  if (e === 'D3') return 1 + Math.floor(Math.random() * 3);
  if (e === 'D6') return 1 + Math.floor(Math.random() * 6);
  const ndm = e.match(/^(\d)D(\d?)$/);
  if (ndm) {
    const count = parseInt(ndm[1], 10);
    const sides = ndm[2] ? parseInt(ndm[2], 10) : 6;
    let total = 0;
    for (let i = 0; i < count; i++) total += 1 + Math.floor(Math.random() * sides);
    return total;
  }
  const n = parseInt(e, 10);
  return isNaN(n) ? 1 : Math.max(1, n);
}

function parseEventAssociateOps(text) {
  // Detect associate mutations in an event. Returns an array of ops, each
  // shaped:
  //   { type:'add',      kinds:['ally']                }           // unambiguous
  //   { type:'add',      kinds:['rival','enemy']       }           // "Gain a Rival or Enemy"
  //   { type:'add',      kinds:['contact','ally']      }           // "Gain a Contact or Ally"
  //   { type:'betrayal', fromKinds:['contact','ally'],
  //                      toKinds:['rival','enemy']     }           // life-event #8
  // Returns [] if no associate mechanics are present. Safe to call on any
  // event text.
  if (!text) return [];
  const ops = [];
  const raw = String(text);

  // Betrayal (life event #8) — highest priority since it mentions both.
  //   "If you have any Contacts or Allies, convert one into a Rival or Enemy.
  //    Otherwise, gain a Rival or an Enemy."
  if (/If you have any Contacts? or Allies?.*?convert one into a Rival or (?:an? )?Enemy/i.test(raw)) {
    ops.push({
      type: 'betrayal',
      fromKinds: ['contact', 'ally'],
      toKinds: ['rival', 'enemy'],
    });
    return ops;  // Betrayal covers the whole event — don't also match the "Otherwise, gain" clause.
  }

  // Pair-disjunction "Gain a Rival or Enemy" / "Gain a Contact or Ally" /
  // "Gain a Rival or an Enemy". The second article is optional because the
  // rulebook wording varies.
  const pairRe = /gain\s+(?:a|an|one)\s+(?:new\s+|another\s+)?(contact|ally|rival|enemy)\s+or\s+(?:a\s+|an\s+|one\s+)?(contact|ally|rival|enemy)/gi;
  let m;
  const consumedRanges = [];
  while ((m = pairRe.exec(raw)) !== null) {
    ops.push({
      type: 'add',
      kinds: [m[1].toLowerCase(), m[2].toLowerCase()],
    });
    consumedRanges.push([m.index, m.index + m[0].length]);
  }

  // Dice-quantity grants: "Gain D3 Contacts" (agent[5]), "Gain 1D Contacts and
  // D3 Enemies" (scout[3]). We accept D3, D6, 1D, 2D, NDN and bare integers.
  // Each match becomes a 'quantity' op; the render layer rolls the die once,
  // caches the result on lr.assocQtyRolls, and expands to N individual add ops.
  const qtyKindMap = {
    contact: 'contact', contacts: 'contact',
    ally: 'ally', allies: 'ally',
    rival: 'rival', rivals: 'rival',
    enemy: 'enemy', enemies: 'enemy',
  };
  const qtyRe = /(?:gain|and)\s+(d3|d6|\dd\d?|[2-6])\s+(contacts?|allies|rivals?|enemies|enemy)\b/gi;
  while ((m = qtyRe.exec(raw)) !== null) {
    const inPrior = consumedRanges.some(([s, e]) => m.index >= s && m.index < e);
    if (inPrior) continue;
    const diceExpr = m[1].toUpperCase();
    const kind = qtyKindMap[m[2].toLowerCase()];
    if (!kind) continue;
    ops.push({ type: 'quantity', kind, diceExpr });
    consumedRanges.push([m.index, m.index + m[0].length]);
  }

  // Single-kind "Gain a Contact" / "Gain an Ally" / "Gain a Rival" / "Gain an Enemy".
  // Allows filler like "new" ("You gain a new Contact.") and trailing
  // qualifiers ("Gain an Ally in the Imperium"). Skips offsets already
  // consumed by the pair regex.
  const singleRe = /gain\s+(?:a|an|one)\s+(?:new\s+|another\s+)?(contact|ally|rival|enemy)(?!\s+or\s+(?:a\s+|an\s+|one\s+)?(?:contact|ally|rival|enemy))/gi;
  while ((m = singleRe.exec(raw)) !== null) {
    const inPair = consumedRanges.some(([s, e]) => m.index >= s && m.index < e);
    if (inPair) continue;
    ops.push({ type: 'add', kinds: [m[1].toLowerCase()] });
  }

  // "as well as a Rival and an Ally" (noble[10]) — trailing grant after a
  // primary skill-level gain. Matches the first associate after the
  // connector; the subsequent "and a/an Y" is picked up by the conjunction
  // loop below.
  const trailRe = /\bas\s+well\s+as\s+(?:a\s+|an\s+|one\s+)(contact|ally|rival|enemy)\b/gi;
  while ((m = trailRe.exec(raw)) !== null) {
    const inPrior = consumedRanges.some(([s, e]) => m.index >= s && m.index < e);
    if (inPrior) continue;
    ops.push({ type: 'add', kinds: [m[1].toLowerCase()] });
    consumedRanges.push([m.index, m.index + m[0].length]);
  }

  // Conjunction pickup: "... and an Enemy" / "... and a Rival" following a
  // prior Gain clause. Covers marine[4] "Gain a Contact (fellow prisoner)
  // and an Enemy" and similar. Only runs if we already parsed something.
  if (ops.length > 0) {
    const andRe = /\band\s+(?:a\s+|an\s+)(contact|ally|rival|enemy)\b/gi;
    while ((m = andRe.exec(raw)) !== null) {
      // Skip if this "and a Contact" already lives inside a pair match
      // (e.g. "Contact or Ally" — we don't want to misread "or" as "and").
      const inPair = consumedRanges.some(([s, e]) => m.index >= s && m.index < e);
      if (inPair) continue;
      // Avoid duplicate: if the exact same kind was already added at a
      // nearby offset (within 12 chars), skip.
      ops.push({ type: 'add', kinds: [m[1].toLowerCase()] });
    }
  }

  return ops;
}

function renderEventStep() {
  // Post-roll view with dice + event text
  if (uiState.lastRoll?.type === 'event') {
    const lr = uiState.lastRoll;
    const grants = Array.isArray(lr.dmGrants) ? lr.dmGrants : [];
    const appliedGrants = grants.filter(g => g.applied);
    const pendingGrants = grants.filter(g => !g.applied);

    const appliedHTML = appliedGrants.length ? `
      <div class="dm-applied-box">
        <span class="event-label">Auto-applied DMs</span>
        ${appliedGrants.map(g => `
          <div class="dm-chip applied">DM${g.dm >= 0 ? '+' : ''}${g.dm} → next ${g.target} roll</div>
        `).join('')}
      </div>
    ` : '';

    // Compute picker state early so pendingHTML knows whether DMs appear inside
    // the picker (reversed pattern: DM first, skill alt) or as a dual-DM choice.
    const _eSkillOpts = parseEventSkillOptions(lr.eventText || '');
    const _eWild = !_eSkillOpts ? parseEventWildcardSkill(lr.eventText || '') : null;
    const _eCareerKey = (character?.current_term?.career_id) || null;
    const _eWildOpts = _eWild ? resolveWildcardSkillOptions(_eWild, _eCareerKey) : null;
    const _eDmAlt = parseEventDmAlternative(lr.eventText || '');
    const _eTransfer = parseEventTransferOffer(lr.eventText || '');
    const _eChosen = lr.eventChoicePath;
    const _ePickerOpts = _eSkillOpts || _eWildOpts;
    const _eShowPicker = !_eChosen && (
      (_ePickerOpts && _ePickerOpts.length > 0) ||
      (_eWild && (_eDmAlt || pendingGrants.length > 0)) ||
      (_eTransfer && !pendingGrants.length)  // transfer alone (no competing DM)
    );
    // DMs embedded as alternatives in the skill picker (prisoner[5] pattern)
    const pendingGrantsInPicker = _eShowPicker && pendingGrants.length > 0 && !_eDmAlt;
    // Competing rewards with no skill picker: DM vs DM, or DM vs transfer
    const showDualChoice = !_eChosen && !_eShowPicker && (
      pendingGrants.length >= 2 ||
      (pendingGrants.length >= 1 && !!_eTransfer)
    );

    const pendingHTML = showDualChoice ? `
      <div class="event-skill-picker">
        <span class="event-label"><strong>PICK ONE</strong></span>
        <div class="skill-picker">
          ${pendingGrants.map(g => `
            <button class="skill-chip dm-alt" data-event-dm="${g.dm}" data-event-dm-target="${escapeHTML(g.target)}">DM${g.dm >= 0 ? '+' : ''}${g.dm} to next ${escapeHTML(g.target)} roll</button>
          `).join('')}
          ${_eTransfer ? `
            <button class="skill-chip dm-alt" data-event-transfer="${escapeHTML(_eTransfer.career_id)}">${
              _eTransfer.career_id === 'any'
                ? 'Transfer to a career of your choice (no qualification roll)'
                : `Transfer to ${escapeHTML(_eTransfer.career_name)} (no qualification roll)`
            }</button>
          ` : ''}
        </div>
      </div>
    ` : (!pendingGrantsInPicker && pendingGrants.length) ? `
      <div class="dm-pending-box">
        <span class="event-label">DM grants (conditional — resolve manually)</span>
        ${pendingGrants.map(g => `
          <div class="dm-chip pending">DM${g.dm >= 0 ? '+' : ''}${g.dm} to ${g.target} roll (if earned)</div>
        `).join('')}
      </div>
    ` : '';

    // Stat bonuses (e.g. entertainer[12] "SOC +1") — auto-applied unconditionally
    // when no conditional markers are present. Surface them so the player can
    // see the characteristic change.
    const statBonuses = Array.isArray(lr.statBonuses) ? lr.statBonuses : [];
    const statAppliedHTML = statBonuses.filter(s => s.applied).length ? `
      <div class="dm-applied-box">
        <span class="event-label">Auto-applied stat changes</span>
        ${statBonuses.filter(s => s.applied).map(s => `
          <div class="dm-chip applied">${s.stat} ${s.from} → ${s.to} (${s.amount >= 0 ? '+' : ''}${s.amount})</div>
        `).join('')}
      </div>
    ` : '';

    // Auto-promotion (event [12]). If the engine bumped rank, show a chip so
    // the player sees it and knows to skip the advancement roll this term.
    const autoProm = lr.autoPromotion || null;
    const autoPromHTML = (autoProm && !autoProm.skipped) ? `
      <div class="dm-applied-box">
        <span class="event-label">Auto-applied promotion</span>
        <div class="dm-chip applied">Rank ${autoProm.from_rank} → ${autoProm.to_rank}${autoProm.rank_title ? ` — ${autoProm.rank_title}` : ''}</div>
        ${autoProm.bonus ? `<div class="dm-chip applied">Rank bonus: ${autoProm.bonus}</div>` : ''}
        <div class="small-hint" style="margin-top:.35rem">No Advancement roll this term — you've already been promoted.</div>
      </div>
    ` : (autoProm && autoProm.skipped ? `
      <div class="dm-applied-box" style="border-color: var(--warning, #ff9); color: var(--warning, #ff9)">
        <span class="event-label">Promotion not applied</span>
        <div class="small-hint">${autoProm.reason === 'rankless_career' ? 'This career has no ranks — treat as "gain a skill instead" per the rulebook.' : autoProm.reason === 'rank_cap' ? `Already at maximum rank (${autoProm.rank}).` : 'Could not auto-promote; apply manually.'}</div>
      </div>
    ` : '');

    // Skill-choice picker — reuse variables computed above for pendingHTML.
    const skillOptions = _eSkillOpts;
    const wildcardSpec = _eWild;
    const wildcardOptions = _eWildOpts;
    const dmAlternative = _eDmAlt;
    const transferOffer = _eTransfer;
    const chosenPath = _eChosen;
    const pickerOptions = _ePickerOpts;
    const wildcardLabel = wildcardSpec ? ({
      'already-have': 'any skill you already have',
      'free': 'any skill of your choice',
      'service': 'any Service Skill',
      'service-or-advanced': 'Service or Advanced Education tables',
      'officer-or-advanced': 'Officer or Advanced Education tables',
      'science': 'any Science specialty',
    }[wildcardSpec.type]) : null;
    const showPicker = _eShowPicker;

    const pickerHTML = showPicker ? `
      <div class="event-skill-picker">
        <span class="event-label">Choose your reward</span>
        ${wildcardLabel ? `<p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>Pick ${escapeHTML(wildcardLabel)}${(pickerOptions && pickerOptions.length) ? '' : ' — none available, take the DM instead'}:</em></p>` : ''}
        <div class="skill-picker">
          ${(pickerOptions || []).map(opt => {
            const display = opt.replace(/\s+\d+\s*$/, '');
            return `<button class="skill-chip" data-event-skill="${escapeHTML(opt)}">+ ${escapeHTML(display)} 1</button>`;
          }).join('')}
          ${dmAlternative ? `
            <button class="skill-chip dm-alt" data-event-dm="${dmAlternative.dm}" data-event-dm-target="${escapeHTML(dmAlternative.target)}">DM${dmAlternative.dm >= 0 ? '+' : ''}${dmAlternative.dm} to next ${escapeHTML(dmAlternative.target)} roll</button>
          ` : ''}
          ${pendingGrantsInPicker ? pendingGrants.map(g =>
            `<button class="skill-chip dm-alt" data-event-dm="${g.dm}" data-event-dm-target="${escapeHTML(g.target)}">DM${g.dm >= 0 ? '+' : ''}${g.dm} to next ${escapeHTML(g.target)} roll</button>`
          ).join('') : ''}
          ${transferOffer ? `
            <button class="skill-chip dm-alt" data-event-transfer="${escapeHTML(transferOffer.career_id)}">${
              transferOffer.career_id === 'any'
                ? `Transfer to a career of your choice (no qualification roll)`
                : `Transfer to ${escapeHTML(transferOffer.career_name)} (no qualification)`
            }</button>
          ` : ''}
        </div>
        <p class="picker-status">Pick one to continue.</p>
      </div>
    ` : '';

    const transferAppliedHTML = lr.eventTransferApplied ? `
      <div class="dm-applied-box">
        <span class="event-label">Transfer accepted</span>
        <div class="dm-chip applied">Transferring to ${escapeHTML(lr.eventTransferApplied)} at term end — no qualification roll.</div>
      </div>
    ` : '';

    // Contested-roll picker: "Roll <Skill> 8+" branches (drifter[6], entertainer[8],
    // navy[3], scholar[9], scout[8]/[9]/[10], rogue[8], prisoner[8]).
    // We offer a button per skill option, and a "Skip — apply manually" fallback.
    const contested = !chosenPath && !lr.eventContestedResolved
      ? parseEventContestedRoll(lr.eventText || '')
      : null;
    // Refuse option (noble[3] duel, noble[8] conspiracy) — only surface alongside
    // a contested roll, since "If you refuse" is always paired with "If you accept, roll ...".
    const refuseOpt = contested && !lr.eventContestedResolved
      ? parseEventRefuseOption(lr.eventText || '')
      : null;
    const refuseChipHTML = refuseOpt ? `<button class="skill-chip dm-alt" data-event-refuse="1" title="${escapeHTML(refuseOpt.consequence)}">Refuse — ${escapeHTML(refuseOpt.consequence)}</button>` : '';
    const contestedHTML = contested ? `
      <div class="event-skill-picker">
        <span class="event-label">Make your check</span>
        <p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)">
          <em>Target: ${contested.target}+ — pick which skill to roll:</em>
        </p>
        <div class="skill-picker">
          ${contested.skills.map((sk, i) => {
            const lvl = getSkillLevelFor(sk.name, sk.speciality);
            const lvlStr = lvl >= 0 ? `+${lvl}` : `${lvl}`;
            const label = sk.speciality ? `${sk.name} (${sk.speciality})` : sk.name;
            return `<button class="skill-chip" data-contested-roll="${i}">Roll ${escapeHTML(label)} ${contested.target}+ (your DM ${lvlStr})</button>`;
          }).join('')}
          ${refuseChipHTML}
        </div>
      </div>
    ` : '';

    const contestedResultHTML = lr.eventContestedResolved ? `
      <div class="dm-applied-box">
        <span class="event-label">${lr.eventContestedResolved.success ? 'Success' : 'Failure'}</span>
        <div class="dm-chip applied">Rolled ${escapeHTML(lr.eventContestedResolved.skillLabel)}: 2D [${lr.eventContestedResolved.dice.join(' · ')}] + ${lr.eventContestedResolved.mod >= 0 ? '+' : ''}${lr.eventContestedResolved.mod} = ${lr.eventContestedResolved.total} vs ${lr.eventContestedResolved.target}+</div>
        ${lr.eventContestedResolved.branchText ? `<div class="small-hint" style="margin-top:.35rem"><em>${escapeHTML(lr.eventContestedResolved.branchText)}</em></div>` : ''}
        ${lr.eventContestedResolved.appliedMsgs && lr.eventContestedResolved.appliedMsgs.length ? lr.eventContestedResolved.appliedMsgs.map(m => `<div class="dm-chip applied">${escapeHTML(m)}</div>`).join('') : ''}
      </div>
    ` : '';

    // Skill picker that appears after a successful contested roll whose success
    // branch grants a skill choice (e.g. navy[8], army[8], marine[8]).
    const csr = lr.eventContestedResolved;
    const contestedSkillPickerHTML = (csr && csr.success && csr.pendingSkillPick && !csr.skillChosen) ? (() => {
      const psp = csr.pendingSkillPick;
      const ckCareer = (character && character.current_term && character.current_term.career_id) || null;
      const opts = psp.options || (psp.wildcardSpec ? resolveWildcardSkillOptions(psp.wildcardSpec, ckCareer) : null);
      const wLabel = psp.wildcardSpec ? ({
        'already-have': 'any skill you already have',
        'free': 'any skill of your choice',
        'service': 'any Service Skill',
        'service-or-advanced': 'Service or Advanced Education tables',
        'officer-or-advanced': 'Officer or Advanced Education tables',
        'science': 'any Science specialty',
      }[psp.wildcardSpec.type] || 'a skill') : null;
      if (!opts || !opts.length) return '';
      return `
        <div class="event-skill-picker">
          <span class="event-label">Choose your reward</span>
          ${wLabel ? `<p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>Pick ${escapeHTML(wLabel)}:</em></p>` : ''}
          <div class="skill-picker">
            ${opts.map(opt => { const dispOpt = opt.replace(/\s+\d+\s*$/, ''); return `<button class="skill-chip" data-contested-skill="${escapeHTML(opt)}">+ ${escapeHTML(dispOpt)} 1</button>`; }).join('')}
          </div>
          <p class="picker-status">Pick one to continue.</p>
        </div>
      `;
    })() : '';

    const skillAppliedHTML = lr.eventSkillApplied ? `
      <div class="dm-applied-box">
        <span class="event-label">Skill chosen</span>
        <div class="dm-chip applied">+ ${escapeHTML(lr.eventSkillApplied)}</div>
      </div>
    ` : '';

    const dmChosenHTML = (chosenPath === 'dm' && lr.eventDmApplied) ? `
      <div class="dm-applied-box">
        <span class="event-label">DM chosen</span>
        <div class="dm-chip applied">DM${lr.eventDmApplied.dm >= 0 ? '+' : ''}${lr.eventDmApplied.dm} → next ${escapeHTML(lr.eventDmApplied.target)} roll</div>
      </div>
    ` : '';

    // Associate outcomes (Gain a Contact/Ally/Rival/Enemy, Betrayal conversion,
    // or dice-quantity grants like "Gain D3 Contacts"). One picker per op;
    // resolved ops render as a "Gained ..." chip instead.
    // Quantity ops (D3/1D/etc.) are pre-rolled once and cached on lr so re-
    // renders don't re-roll. Each quantity op then expands into N add ops.
    // When a contested roll (skill check) has been resolved, only parse
    // associates from the relevant branch text. Parsing the full event text
    // would pick up associates from BOTH the success and failure branches,
    // awarding e.g. both a Contact (success) and an Enemy (failure) regardless
    // of the actual outcome. If no contested roll exists, parse the full text.
    const _csr = lr.eventContestedResolved;
    const _assocSourceText = (_csr && _csr.success !== null && _csr.success !== undefined)
      ? (_csr.branchText || '')
      : (lr.eventText || '');
    const rawAssociateOps = parseEventAssociateOps(_assocSourceText);
    if (!Array.isArray(lr.assocQtyRolls)) lr.assocQtyRolls = [];
    const associateOps = [];
    rawAssociateOps.forEach((op, rawIdx) => {
      if (op.type === 'quantity') {
        let n = lr.assocQtyRolls[rawIdx];
        if (n == null || n < 1) {
          n = rollAssocQuantity(op.diceExpr);
          lr.assocQtyRolls[rawIdx] = n;
        }
        for (let i = 0; i < n; i++) {
          associateOps.push({
            type: 'add',
            kinds: [op.kind],
            qtyMeta: { diceExpr: op.diceExpr, rolled: n, slot: i + 1, of: n },
          });
        }
      } else {
        associateOps.push(op);
      }
    });
    const assocDone = Array.isArray(lr.associateOpsDone) ? lr.associateOpsDone : [];
    const pendingAssocOps = associateOps.map((op, idx) => ({ op, idx })).filter(({ idx }) => !assocDone[idx]);

    const assocLabel = (k) => ({contact:'Contact', ally:'Ally', rival:'Rival', enemy:'Enemy'}[k] || k);

    const assocSummaryHTML = assocDone.filter(Boolean).length ? `
      <div class="dm-applied-box">
        <span class="event-label">Associates updated</span>
        ${assocDone.filter(Boolean).map(done => `
          <div class="dm-chip applied">${escapeHTML(done)}</div>
        `).join('')}
      </div>
    ` : '';

    const existingContactsAllies = (character.associates || [])
      .map((a, i) => ({ a, i }))
      .filter(({ a }) => a.kind === 'contact' || a.kind === 'ally');

    const associatePickerHTML = pendingAssocOps.length ? `
      <div class="event-skill-picker associate-picker">
        <span class="event-label">Resolve associate outcome${pendingAssocOps.length > 1 ? 's' : ''}</span>
        ${pendingAssocOps.map(({ op, idx }) => {
          if (op.type === 'add') {
            const qm = op.qtyMeta;
            const prompt = qm
              ? `Gain a ${assocLabel(op.kinds[0])} <span class="assoc-roll-badge">rolled ${qm.diceExpr} = ${qm.rolled} — ${qm.slot} of ${qm.of}</span>`
              : (op.kinds.length > 1
                  ? `Gain a ${op.kinds.map(assocLabel).join(' or ')} — pick one:`
                  : `Gain a ${assocLabel(op.kinds[0])}:`);
            return `
              <div class="assoc-op" data-assoc-op-idx="${idx}">
                <div class="assoc-op-prompt">${prompt}</div>
                <input type="text" class="assoc-desc-input" data-assoc-desc="${idx}" placeholder="Who are they? (name or short note — optional)" />
                <div class="skill-picker">
                  ${op.kinds.map(k => `
                    <button class="skill-chip" data-assoc-add="${idx}" data-assoc-kind="${k}">+ Add ${assocLabel(k)}</button>
                  `).join('')}
                </div>
              </div>
            `;
          }
          if (op.type === 'betrayal') {
            const hasAny = existingContactsAllies.length > 0;
            return `
              <div class="assoc-op" data-assoc-op-idx="${idx}">
                <div class="assoc-op-prompt">Betrayal — ${hasAny
                  ? `convert an existing Contact or Ally into a Rival or Enemy:`
                  : `no Contacts or Allies to convert — gain a Rival or Enemy instead:`}</div>
                ${hasAny ? `
                  <div class="assoc-convert-list">
                    ${existingContactsAllies.map(({ a, i }) => `
                      <div class="assoc-row">
                        <span class="assoc-label assoc-kind-${a.kind}">[${assocLabel(a.kind)}]</span>
                        <span class="assoc-desc">${escapeHTML(a.description || '(no description)')}</span>
                        <span class="skill-picker inline">
                          <button class="skill-chip danger" data-assoc-convert="${idx}" data-assoc-index="${i}" data-assoc-to="rival">→ Rival</button>
                          <button class="skill-chip danger" data-assoc-convert="${idx}" data-assoc-index="${i}" data-assoc-to="enemy">→ Enemy</button>
                        </span>
                      </div>
                    `).join('')}
                  </div>
                  <div class="assoc-op-prompt" style="margin-top:8px">…or instead, add a new one:</div>
                ` : ''}
                <input type="text" class="assoc-desc-input" data-assoc-desc="${idx}" placeholder="Who are they? (name or short note — optional)" />
                <div class="skill-picker">
                  <button class="skill-chip" data-assoc-add="${idx}" data-assoc-kind="rival">+ Add Rival</button>
                  <button class="skill-chip" data-assoc-add="${idx}" data-assoc-kind="enemy">+ Add Enemy</button>
                </div>
              </div>
            `;
          }
          return '';
        }).join('')}
        <p class="picker-status">Resolve each associate outcome to continue.</p>
      </div>
    ` : '';

    // Mishap-forcing events (e.g. "Disaster! Roll on the Mishap Table, but you
    // are not ejected from this career.") route the player into the mishap
    // table inline. If the text says "not ejected", they continue the career
    // after the mishap resolves; otherwise the normal end-career flow applies.
    // forcesMishap: the event involves a mishap-table roll, BUT only when there
    // is no contested roll that already succeeded. If the player passed the
    // Electronics check (or similar), the "If you fail, roll on the Mishap Table"
    // clause does NOT apply.
    const rawForcesMishap = /Roll on the Mishap Table/i.test(lr.eventText || '');
    const contestedSucceededForMishap = lr.eventContestedResolved && lr.eventContestedResolved.success === true;
    const forcesMishap = rawForcesMishap && !contestedSucceededForMishap;
    const pendingMishapRoll = forcesMishap && !lr.mishapFromEvent;
    const mishapRolledHTML = (forcesMishap && lr.mishapFromEvent) ? `
      <div class="mishap-box">
        <span class="event-label">Mishap [1D=${lr.mishapFromEvent.total ?? '?'}]</span>
        ${escapeHTML(lr.mishapFromEvent.text || '')}
        ${lr.mishapFromEvent.frozenWatch ? `
          <p class="small-hint" style="margin-top:8px;color:var(--amber-dim)"><em>Frozen Watch — you are preserved in cryo. Career continues; no advancement or skill roll this term.</em></p>
        ` : `
          <p class="small-hint" style="margin-top:8px;color:var(--danger)"><em>A mishap ends your career.</em></p>
        `}
      </div>
    ` : '';

    // Entertainer event 5: two-stage associate picker (type + person category).
    const isEntertainerEv5 = /Contact, Ally, Rival or Enemy \(your choice\)/i.test(lr.eventText || '');
    const entertainerAssocHTML = (isEntertainerEv5 && !lr.entertainerAssocDone) ? (() => {
      const stage1 = lr.entertainerAssocType || null;
      const stage2 = lr.entertainerPersonType || null;
      if (!stage1) return `
        <div class="event-skill-picker">
          <span class="event-label">What kind of relationship? (step 1 of 2)</span>
          <div class="skill-picker">
            ${['contact','ally','rival','enemy'].map(k =>
              `<button class="skill-chip" data-ent-assoc-type="${k}">${k.charAt(0).toUpperCase()+k.slice(1)}</button>`
            ).join('')}
          </div>
        </div>`;
      if (!stage2) return `
        <div class="event-skill-picker">
          <span class="event-label">Who are they? (step 2 of 2 — ${stage1})</span>
          <div class="skill-picker">
            ${['Celebrity','Noble','Criminal'].map(p =>
              `<button class="skill-chip" data-ent-assoc-person="${p}">${p}</button>`
            ).join('')}
          </div>
        </div>`;
      return `
        <div class="dm-applied-box">
          <span class="event-label">Ready to confirm</span>
          <div class="dm-chip applied">${stage1.charAt(0).toUpperCase()+stage1.slice(1)}: ${stage2} — Entertainer event</div>
          <div class="skill-picker" style="margin-top:6px">
            <button class="skill-chip" id="btn-ent-assoc-confirm">CONFIRM</button>
          </div>
        </div>`;
    })() : (isEntertainerEv5 && lr.entertainerAssocDone) ? `
      <div class="dm-applied-box">
        <span class="event-label">Associate added</span>
        <div class="dm-chip applied">${escapeHTML(lr.entertainerAssocDone)}</div>
      </div>` : '';

    // Citizen event 8: retroactive survival check warning.
    const citizenEv8HTML = lr.citizenEv8SurvivalFailed ? `
      <div class="mishap-box">
        <span class="event-label">Retroactive Survival Failure</span>
        <p style="margin:4px 0">DM-2 to your survival roll would have caused a failure. You must resolve a Mishap instead of continuing the event.</p>
        <div class="phase-actions" style="margin-top:8px">
          <button class="btn danger" id="btn-citizen-ev8-mishap">RESOLVE MISHAP INSTEAD →</button>
        </div>
      </div>` : '';

    // Prisoner event 7: parole button after successful contested roll.
    const prisonerParoleHTML = lr.prisonerParoleGranted && !lr.prisonerParoleTaken ? `
      <div class="dm-applied-box">
        <span class="event-label">Parole Granted</span>
        <p style="margin:4px 0 8px">You leave this career at the end of the term with no penalty.</p>
        <button class="btn primary" id="btn-prisoner-parole">ACCEPT PAROLE — LEAVE CAREER →</button>
      </div>` : '';

    // Scout event 2: show ban confirmation after failure.
    const scoutBanHTML = lr.scoutBanned ? `
      <div class="dm-applied-box" style="border-color:var(--danger)">
        <span class="event-label" style="color:var(--danger)">Re-enlistment Banned</span>
        <div class="dm-chip applied">SCOUT career removed from future options</div>
      </div>` : '';

    const entertainerPending = isEntertainerEv5 && !lr.entertainerAssocDone;
    const citizenMishapPending = !!lr.citizenEv8SurvivalFailed;

    const gateAdvance = !!(showPicker && !chosenPath) || pendingMishapRoll || pendingAssocOps.length > 0
      || !!(csr && csr.success && csr.pendingSkillPick && !csr.skillChosen)
      || entertainerPending || citizenMishapPending;

    // Action row varies by what's happening:
    // - Pending forced mishap roll: show ROLL MISHAP
    // - Forced mishap rolled, Frozen Watch: career continues (no advancement this term)
    // - Forced mishap rolled, anything else: career ENDS — show END CAREER
    // - Citizen ev8 survival failed: show mishap button (handled inline above)
    // - Normal flow: show ATTEMPT advancement
    const actionsHTML = pendingMishapRoll ? `
      <button class="btn danger" id="btn-event-forced-mishap">ROLL ON MISHAP TABLE →</button>
    ` : (forcesMishap && lr.mishapFromEvent && lr.mishapFromEvent.frozenWatch) ? `
      <button class="btn primary" id="btn-post-event"${gateAdvance ? ' disabled' : ''}>FROZEN WATCH — CONTINUE →</button>
    ` : (forcesMishap && lr.mishapFromEvent) ? `
      <button class="btn danger" id="btn-post-mishap">END CAREER →</button>
    ` : `
      <button class="btn primary" id="btn-post-event"${gateAdvance ? ' disabled' : ''}>ATTEMPT ADVANCEMENT →</button>
    `;

    return `
      <div class="stage-content">
        <div class="phase-label">Event Roll</div>
        <h2 class="phase-title">Something Happened</h2>
        ${rollReadoutHTML(lr.data, { label: '2D', showTarget: false })}
        <div class="event-box">
          <span class="event-label">Event [2D=${lr.data?.total ?? '?'}]</span>
          ${escapeHTML(lr.eventText || '')}
        </div>
        ${appliedHTML}
        ${pendingHTML}
        ${statAppliedHTML}
        ${autoPromHTML}
        ${pickerHTML}
        ${contestedHTML}
        ${contestedResultHTML}
        ${contestedSkillPickerHTML}
        ${skillAppliedHTML}
        ${dmChosenHTML}
        ${transferAppliedHTML}
        ${associatePickerHTML}
        ${assocSummaryHTML}
        ${mishapRolledHTML}
        ${(() => {
          // Agent event 8: cross-career roll on Rogue or Citizen event/mishap table
          if (!(lr.eventText || '').includes('Rogue or Citizen')) return '';
          if (!lr.eventContestedResolved) return '';  // wait for contested roll first
          const succeeded = lr.eventContestedResolved.success;
          const tbl = succeeded ? 'event' : 'mishap';
          if (lr.crossCareerResult) {
            return `
              <div class="event-box" style="margin-top:12px">
                <span class="event-label">${escapeHTML(lr.crossCareerResult.career_name)} ${tbl === 'event' ? 'Event' : 'Mishap'} [${tbl === 'event' ? '2D' : '1D'}=${lr.crossCareerResult.roll?.total ?? '?'}]</span>
                ${escapeHTML(lr.crossCareerResult.text || '')}
              </div>`;
          }
          return `
            <div class="event-box" style="margin-top:12px">
              <p class="phase-body"><strong>Roll on which career's ${tbl} table?</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-cross-career-rogue">ROGUE</button>
                <button class="btn" id="btn-cross-career-citizen">CITIZEN</button>
              </div>
            </div>`;
        })()}
        ${entertainerAssocHTML}
        ${citizenEv8HTML}
        ${prisonerParoleHTML}
        ${scoutBanHTML}
        ${showPicker || (contested && !lr.eventContestedResolved) || (csr && csr.success && csr.pendingSkillPick && !csr.skillChosen) || forcesMishap || associateOps.length || (autoProm && !autoProm.skipped) || isEntertainerEv5 ? '' : `<p class="phase-body empty"><em>Apply any resulting benefits manually to your notes — only "DM+N to next X roll" grants and stat changes are auto-applied.</em></p>`}
        <div class="phase-actions">
          ${actionsHTML}
        </div>
      </div>
    `;
  }

  return `
    <div class="stage-content">
      <div class="phase-label">Event Table · 2D Roll</div>
      <h2 class="phase-title">What Happened This Term?</h2>
      <p class="phase-body">Roll 2D on the Events table. Could be anything from an ambush to a promotion.</p>
      <div class="phase-actions">
        <button class="btn primary" id="btn-event">ROLL EVENT</button>
      </div>
    </div>
  `;
}

function renderMishapStep() {
  if (uiState.lastRoll?.type === 'mishap') {
    const lr = uiState.lastRoll;

    // ---- Frozen Watch: character stays in service, continue to next term ----
    if (lr.frozenWatch) {
      return `
        <div class="stage-content">
          <div class="phase-label">Mishap [1D=${lr.data?.total ?? '?'}] — FROZEN WATCH</div>
          <h2 class="phase-title">Frozen Watch</h2>
          ${rollReadoutHTML(lr.data, { label: '1D', showTarget: false })}
          <div class="mishap-box">
            <span class="event-label">Mishap [1D=2] — Frozen Watch</span>
            ${escapeHTML(lr.mishapText || '')}
          </div>
          <div class="event-box" style="margin-top:12px;border-color:var(--accent)">
            <span class="event-label" style="color:var(--accent)">STAYING IN SERVICE</span>
            You are not ejected from the Confederation Navy. No skill or advancement roll
            this term. You may automatically re-enlist next term.
          </div>
          <div class="phase-actions" style="margin-top:16px">
            <button class="btn primary" id="btn-frozen-watch-continue">CONTINUE IN SERVICE →</button>
          </div>
        </div>
      `;
    }

    const pending = character.pending_career_mishap_choice;
    const injPending = character.pending_injury_choice;
    const statDescs = { STR: 'Strength', DEX: 'Dexterity', END: 'Endurance', INT: 'Intellect', EDU: 'Education', SOC: 'Social' };

    // Auto-applied chips
    let autoHtml = '';
    if (lr.autoApplied && lr.autoApplied.length) {
      const chips = lr.autoApplied.map(a => `<span class="skill-chip dm-chip">${escapeHTML(a)}</span>`).join('');
      autoHtml = `<div class="dm-applied-box" style="margin-top:10px">${chips}</div>`;
    }

    // Injury data box (from auto-resolved injury effect)
    let injDataHtml = '';
    if (lr.injuryTitle) {
      const injRollLabel = lr.injuryRoll != null ? ` [Injury Table 1D=${lr.injuryRoll}]` : '';
      injDataHtml = `
        <div class="event-box" style="margin-top:12px">
          <span class="event-label">Injury Table${injRollLabel} — ${escapeHTML(lr.injuryTitle)}</span>
          ${escapeHTML(lr.injuryText || '')}
        </div>`;
    }

    // Pending choice UI
    let pendingHtml = '';
    if (pending) {
      const ptype = pending.type;
      const pprompt = pending.prompt || '';

      if (ptype === 'injury_severity_choice') {
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>Choose how to handle this injury:</strong></p>
            <div class="phase-actions" style="margin-top:8px">
              <button class="btn" id="btn-mishap-choice-result2">TAKE RESULT 2 (GRIEVOUS INJURY)</button>
              <button class="btn" id="btn-mishap-choice-roll-twice">ROLL TWICE, TAKE LOWER</button>
            </div>
          </div>`;
      } else if (ptype === 'stat_choice') {
        const opts = (pending.options || []).map(stat => `
          <button class="card" id="btn-mishap-statchoice-${stat}">
            <div class="card-title">${stat} — ${statDescs[stat] || stat}</div>
            <div class="card-meta">Current: ${character.characteristics[stat] ?? '?'}</div>
            <div class="card-desc">Reduce by ${Math.abs(pending.amount || 1)}</div>
          </button>`).join('');
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
            <div class="card-grid">${opts}</div>
          </div>`;
      } else if (ptype === 'skill_choice') {
        const options = pending.options || [];
        if (options.length > 0) {
          // Specific options — show as buttons
          const opts = options.map(sk =>
            `<button class="btn" id="btn-mishap-skillchoice-${escapeHTML(sk)}">${escapeHTML(sk)}</button>`).join('');
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">${opts}</div>
            </div>`;
        } else {
          // Any skill — show comprehensive grid picker
          const allSkills = ['Admin','Advocate','Animals','Art','Astrogation','Athletics','Broker',
            'Carouse','Deception','Diplomat','Drive','Electronics','Engineer','Explosives','Flyer',
            'Gambler','Gun Combat','Gunner','Heavy Weapons','Investigate','Jack-of-All-Trades',
            'Language','Leadership','Mechanic','Medic','Melee','Navigation','Persuade','Pilot',
            'Profession','Recon','Science','Seafarer','Stealth','Steward','Streetwise','Survival',
            'Tactics','Vacc Suit'];
          const chips = allSkills.map(sk =>
            `<button class="skill-chip ${CASCADE_SKILLS[sk] ? 'cascade' : ''}" data-mishap-anyskill="${escapeHTML(sk)}">${escapeHTML(sk)}${CASCADE_SKILLS[sk] ? ' ▸' : ''}</button>`
          ).join('');
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="skill-picker" style="margin-top:8px">${chips}</div>
            </div>`;
        }
      } else if (ptype === 'free_skill_choice') {
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
            <div style="display:flex;gap:8px;margin-top:8px;align-items:center">
              <input type="text" id="input-mishap-freeskill" placeholder="Skill name…" style="flex:1;padding:6px 10px;background:var(--surface2);border:1px solid var(--amber-dim);color:var(--text);border-radius:4px"/>
              <button class="btn" id="btn-mishap-freeskill-confirm">CONFIRM</button>
            </div>
          </div>`;
      } else if (ptype === 'pending_choice') {
        const pid = pending.id || '';
        if (pid === 'mishap_deal') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-deal-accept">ACCEPT DEAL</button>
                <button class="btn danger" id="btn-mishap-deal-refuse">REFUSE — FIGHT BACK</button>
              </div>
            </div>`;
        } else if (pid === 'army_join_cooperate') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-armyjoin-join">JOIN THEIR RING</button>
                <button class="btn" id="btn-mishap-armyjoin-cooperate">CO-OPERATE WITH POLICE</button>
              </div>
            </div>`;
        } else if (pid === 'solsec_blame') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-blame-pin">PIN BLAME ON A COLLEAGUE</button>
                <button class="btn danger" id="btn-mishap-blame-fall">TAKE THE FALL</button>
              </div>
            </div>`;
        } else if (pid === 'solsec_expose') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-expose-yes">EXPOSE THE TRAITOR</button>
                <button class="btn danger" id="btn-mishap-expose-no">STAY QUIET</button>
              </div>
            </div>`;
        } else if (pid === 'party_denounce') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-denounce-yes">DENOUNCE PATRON</button>
                <button class="btn danger" id="btn-mishap-denounce-no">STAY SILENT</button>
              </div>
            </div>`;
        } else if (pid === 'solsec_interrogation') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn danger" id="btn-mishap-interrogation-submit">SUBMIT TO INTERROGATION</button>
                <button class="btn" id="btn-mishap-interrogation-refuse">REFUSE — ROLL END 8+</button>
              </div>
            </div>`;
        } else if (pid === 'mishap_victim') {
          const opts = (pending.options || []);
          if (opts.length === 0) {
            pendingHtml = `
              <div class="event-box" style="margin-top:14px">
                <p class="phase-body"><em>No contacts or allies to target — mishap effect skipped.</em></p>
                <div class="phase-actions" style="margin-top:8px">
                  <button class="btn" id="btn-mishap-victim-skip">CONTINUE</button>
                </div>
              </div>`;
          } else {
            const btns = opts.slice(0, 5).map(o => `
              <button class="btn" id="btn-mishap-victim-${o.associate_index}"
                data-assoc-idx="${o.associate_index}">${escapeHTML(o.label)}</button>`).join('');
            pendingHtml = `
              <div class="event-box" style="margin-top:14px">
                <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
                <div class="phase-actions" style="margin-top:8px;flex-direction:column;align-items:flex-start">${btns}</div>
              </div>`;
          }
        }
      } else if (ptype === 'skill_check') {
        const skills = (pending.skills || []).map(s => `
          <button class="btn" id="btn-mishap-skillcheck-${escapeHTML(s.name)}"
            data-skill="${escapeHTML(s.name)}">${escapeHTML(s.name)}</button>`).join('');
        pendingHtml = `
          <div class="event-box" style="margin-top:14px">
            <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
            <p style="font-size:11px;color:var(--amber-dim)">Choose the skill to roll with (2D + skill DM vs ${pending.target || 8}+).</p>
            <div class="phase-actions" style="margin-top:8px">${skills}</div>
          </div>`;
      }
    }

    // Skill check result (if stored after resolve)
    let skillCheckHtml = '';
    if (lr.skillCheckResult) {
      const sc = lr.skillCheckResult;
      skillCheckHtml = `
        <div class="event-box" style="margin-top:12px">
          <span class="event-label">Skill Check — ${escapeHTML(sc.skill)}</span>
          2D=${sc.raw_2d}, DM${sc.dm >= 0 ? '+' : ''}${sc.dm} = <strong>${sc.total}</strong> vs ${sc.target}+ —
          <strong style="color:${sc.passed ? 'var(--success,#4caf50)' : 'var(--danger)'}">${sc.passed ? 'PASS' : 'FAIL'}${sc.nat2 ? ' (Natural 2!)' : ''}</strong>
        </div>`;
    }

    // Injury stat picker (pending_injury_choice)
    let injPickerHtml = '';
    if (injPending) {
      const inj = injPending;
      const choices = inj.choices || ['STR', 'DEX', 'END'];
      const injTableRoll = lr.injuryRoll != null ? ` (Injury Table 1D=${lr.injuryRoll})` : '';
      const cards = choices.map(stat => `
        <button class="card" id="btn-career-injury-stat-${stat}">
          <div class="card-title">${stat} — ${statDescs[stat] || stat}</div>
          <div class="card-meta">Current: ${character.characteristics[stat] ?? '?'}</div>
          <div class="card-desc">Damage: −${inj.damage_to_chosen}${inj.auto_reduce_others ? ` to ${stat}, −${inj.auto_reduce_others} to other two` : ''}. Then choose: accept stat loss (free) OR pay medical debt to keep stats.</div>
        </button>`).join('');
      injPickerHtml = `
        <p class="phase-body" style="margin-top:14px"><strong>${escapeHTML(inj.prompt || 'Choose which stat takes the damage.')}${injTableRoll}</strong></p>
        <p style="font-size:11px;color:var(--amber-dim)">Pick which stat absorbs the hit. You'll then choose: accept permanent stat loss (free) OR pay medical debt to keep stats intact.</p>
        <div class="card-grid">${cards}</div>`;
    }

    // Treatment choice (after stat was chosen, before damage applied)
    const injTreatmentPending = lr.treatmentPending || !!character.pending_injury_treatment_choice;
    let injTreatmentHtml = '';
    if (injTreatmentPending && character.pending_injury_treatment_choice) {
      injTreatmentHtml = renderInjuryTreatmentChoiceHTML(character.pending_injury_treatment_choice, 'career-treatment');
    }

    const canEnd = !pending && !injPending && !injTreatmentPending;

    return `
      <div class="stage-content">
        <div class="phase-label">Mishap</div>
        <h2 class="phase-title">What Went Wrong</h2>
        ${rollReadoutHTML(lr.data, { label: '1D', showTarget: false })}
        <div class="mishap-box">
          <span class="event-label">Mishap [1D=${lr.data?.total ?? '?'}]</span>
          ${escapeHTML(lr.mishapText || '')}
          ${(!lr.injuryPending && !character.pending_career_mishap_choice && !(lr.autoApplied && lr.autoApplied.length)) ? `
            <p class="small-hint" style="margin-top:8px;color:var(--muted)">Career ends — no further mechanical effects apply.</p>
          ` : ''}
        </div>
        ${autoHtml}
        ${injDataHtml}
        ${pendingHtml}
        ${skillCheckHtml}
        ${injPickerHtml}
        ${injTreatmentHtml}
        ${canEnd ? anagathicsBoxHTML('btn-mishap-buy-anagathics') : ''}
        <div class="phase-actions" style="margin-top:16px">
          ${canEnd ? `<button class="btn danger" id="btn-post-mishap">END CAREER →</button>` : ''}
        </div>
      </div>
    `;
  }

  return `
    <div class="stage-content">
      <div class="phase-label">Mishap Table · 1D Roll</div>
      <h2 class="phase-title">You Failed to Survive</h2>
      <p class="phase-body">A mishap ends your career. Roll 1D to see what went wrong.</p>
      <div class="phase-actions">
        <button class="btn danger" id="btn-mishap">ROLL MISHAP</button>
      </div>
    </div>
  `;
}

function renderAdvanceStep() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const assignment = career.assignments[term.assignment_id];
  const a = assignment.advancement;
  const advDm = charDM(character.characteristics[a.characteristic]);

  // Commission eligibility
  const hasCommission = !!career.commission;
  // Commissioned this term OR any prior term in the same career
  const alreadyCommissioned = term.commissioned ||
    (character.term_history || []).some(t => t.career_id === term.career_id && t.commissioned);
  const soc = character.characteristics?.SOC ?? 0;
  const commEligible = hasCommission && !alreadyCommissioned &&
    (term.term_number === 1 || soc >= 9);
  const commTarget = career.commission?.target ?? 8;
  const commChar  = career.commission?.characteristic ?? 'SOC';
  const commDm = charDM(character.characteristics[commChar]);
  const termPenaltyDm = -(term.term_number - 1);  // DM-1 per term after first

  // Decide-phase actions (shared by advance result and already-rolled views)
  const _forcedNext = character.forced_next_career_id || null;
  const _forcedNextName = _forcedNext ? (CAREERS.find(c => c.id === _forcedNext)?.name || _forcedNext) : null;
  const decideActions = _forcedNext ? `
    <div class="event-box" style="border-color:var(--danger);margin-top:14px">
      <span class="event-label" style="color:var(--danger)">⚠ MANDATORY — ${_forcedNextName.toUpperCase()}</span>
      A conviction (or equivalent) forces you into the <strong>${_forcedNextName}</strong> career next term.
      You cannot muster out or continue in your current career until you serve this term.
    </div>
    <div class="phase-actions" style="margin-top:12px">
      <button class="btn danger" id="btn-enter-forced-career">SERVE YOUR SENTENCE →</button>
    </div>
    ${anagathicsBoxHTML('btn-advance-buy-anagathics')}
  ` : `
    <div class="phase-actions">
      <button class="btn primary" id="btn-next-term">ANOTHER TERM →</button>
      <button class="btn" id="btn-leave-career">MUSTER OUT</button>
    </div>
    ${anagathicsBoxHTML('btn-advance-buy-anagathics')}
  `;

  // ── Commission result view ───────────────────────────────────
  if (uiState.lastRoll?.type === 'commission') {
    const lr = uiState.lastRoll;
    return `
      <div class="stage-content">
        <div class="phase-label">Commission Roll — ${lr.succeeded ? 'COMMISSIONED' : 'FAILED'}</div>
        <h2 class="phase-title" style="color:${lr.succeeded ? 'var(--success,#7fd87f)' : 'var(--danger)'}">
          ${lr.succeeded
            ? `Commissioned! Rank 1${lr.newRankTitle ? ` — ${lr.newRankTitle}` : ''}`
            : 'Commission Failed'}
        </h2>
        ${rollReadoutHTML(lr.data, { label: `${commChar} ${commTarget}+` })}
        ${lr.succeeded ? `
          <div class="event-box" style="border-color:var(--success,#7fd87f);margin-top:12px">
            <span class="event-label" style="color:var(--success,#7fd87f)">OFFICER — RANK 1</span>
            You are now commissioned. You may not roll for advancement this term.
            ${lr.rankBonus ? `<br>Rank bonus: ${escapeHTML(lr.rankBonus)}` : ''}
          </div>
          <p class="phase-body" style="margin-top:12px">Term complete. Continue or muster out?</p>
          ${decideActions}
        ` : `
          <p class="phase-body">Commission failed. You may still roll for advancement this term.</p>
          <div class="phase-actions">
            <button class="btn primary" id="btn-advance">ROLL FOR ADVANCEMENT</button>
          </div>
        `}
      </div>
    `;
  }

  // ── Advancement result view ──────────────────────────────────
  if (uiState.lastRoll?.type === 'advance') {
    const lr = uiState.lastRoll;
    const advanced = lr.outcome === 'pass';
    const forcedOut = lr.forcedFromCareer || false;
    const advDecideActions = forcedOut ? `
      <div class="event-box" style="border-color:var(--danger);margin-top:12px">
        <span class="event-label" style="color:var(--danger)">FORCED OUT</span>
        Your advancement roll (${lr.data?.total ?? '?'}) is less than your terms served (${term.term_number}) — you must leave this career.
      </div>
      <div class="phase-actions" style="margin-top:12px">
        <button class="btn" id="btn-leave-career">MUSTER OUT →</button>
      </div>
    ` : decideActions;

    // If advanced and bonus skill roll still pending
    if (advanced && uiState.pendingAdvancementSkill) {
      const advCareer = CAREERS.find(c => c.id === term.career_id);
      const advTables = advCareer?.skill_tables || {};
      const advAvailable = Object.entries(advTables).filter(([key, t]) => {
        if (t.assignment_only && t.assignment_only !== term.assignment_id) return false;
        if (t.requires_commission && !term.commissioned) return false;
        return true;
      });
      const advSkillBtns = advAvailable.map(([key, t]) => {
        const gated = t.requires_edu && character.characteristics.EDU < t.requires_edu;
        const previewItems = [1,2,3,4,5,6].map(n => {
          const entry = t[String(n)];
          if (!entry) return '';
          const isStatBump = /^(STR|DEX|END|INT|EDU|SOC|PSI)\s*[+-]\d+$/i.test(String(entry).trim());
          return `<span class="stable-preview-cell ${isStatBump ? 'is-stat' : ''}"><span class="stable-preview-n">${n}</span><span class="stable-preview-v">${escapeHTML(String(entry))}</span></span>`;
        }).join('');
        return `<button class="btn skill-table-btn ${gated ? 'ghost' : ''}" data-adv-skill-table="${key}" ${gated ? 'disabled' : ''}><span class="stable-name">${t.name || key}${t.requires_edu ? ` <span class="stable-req">(EDU ${t.requires_edu}+)</span>` : ''}</span>${previewItems ? `<span class="stable-preview">${previewItems}</span>` : ''}</button>`;
      }).join('');
      return `
        <div class="stage-content">
          <div class="phase-label">Advancement — Promoted · Bonus Skill Roll</div>
          <h2 class="phase-title">Promoted to Rank ${lr.newRank}${lr.newRankTitle ? ` — ${lr.newRankTitle}` : ''}</h2>
          ${rollReadoutHTML(lr.data, { label: `${a.characteristic} ${a.target}+` })}
          <div class="event-box" style="border-color:var(--success,#7fd87f);margin-top:12px">
            <span class="event-label" style="color:var(--success,#7fd87f)">ADVANCEMENT BONUS</span>
            Promotion grants an additional skill roll. Pick a table:
          </div>
          <div style="margin-top:10px;display:flex;flex-direction:column;gap:8px">${advSkillBtns}</div>
        </div>
      `;
    }

    return `
      <div class="stage-content">
        <div class="phase-label">Advancement — ${advanced ? 'Promoted' : 'No Change'}</div>
        <h2 class="phase-title">${advanced
          ? `Promoted to Rank ${lr.newRank}${lr.newRankTitle ? ` — ${lr.newRankTitle}` : ''}`
          : 'No Advancement This Term'}</h2>
        ${rollReadoutHTML(lr.data, { label: `${a.characteristic} ${a.target}+` })}
        ${lr.advancementSkillGained ? `
          <div class="event-box" style="border-color:var(--success,#7fd87f);margin-top:10px">
            <span class="event-label" style="color:var(--success,#7fd87f)">BONUS SKILL GAINED</span>
            ${escapeHTML(lr.advancementSkillGained)}
          </div>` : ''}
        <p class="phase-body">You've completed Term ${term.overall_term_number}. Continue in this career or muster out?</p>
        ${advDecideActions}
      </div>
    `;
  }

  if (term.advanced === null || term.advanced === undefined) {
    // Not yet rolled — show commission option if eligible, then advancement
    return `
      <div class="stage-content">
        <div class="phase-label">${commEligible ? 'Commission / ' : ''}Advancement · 2D Roll</div>
        <h2 class="phase-title">${commEligible ? 'Commission or Advancement?' : 'Advancement Roll'}</h2>

        ${commEligible ? `
          <div class="event-box" style="border-color:var(--amber);margin-top:12px">
            <span class="event-label">COMMISSION AVAILABLE — ${commChar} ${commTarget}+</span>
            Roll to become a Rank 1 officer. Your ${commChar} DM: ${formatDM(commDm)}${termPenaltyDm ? `, term penalty DM${termPenaltyDm}` : ''}.
            <br><em>Success: commissioned, no advancement roll this term. Failure: may still roll for advancement.</em>
            ${term.term_number > 1 ? `<br><span style="color:var(--amber-dim);font-size:11px">SOC 9+ required after first term (your SOC: ${soc}).</span>` : ''}
          </div>
          <div class="phase-actions" style="margin-top:12px">
            <button class="btn primary" id="btn-commission">ROLL FOR COMMISSION</button>
            <button class="btn" id="btn-advance">ROLL FOR ADVANCEMENT ONLY</button>
          </div>
        ` : `
          <p class="phase-subtitle">${a.characteristic} ${a.target}+ (your DM is ${formatDM(advDm)})</p>
          <p class="phase-body">A successful roll promotes you by one rank. If you fail, your career continues — you just don't advance this term.</p>
          <div class="phase-actions">
            <button class="btn primary" id="btn-advance">ROLL FOR ADVANCEMENT</button>
          </div>
        `}
      </div>
    `;
  }

  // Already rolled (restored from session — roll data no longer available)
  return `
    <div class="stage-content">
      <div class="phase-label">Term ${term.overall_term_number} Complete</div>
      <h2 class="phase-title">${term.commissioned ? `Commissioned — Rank ${term.rank}${term.rank_title ? ` — ${term.rank_title}` : ''}` : term.advanced ? `Promoted to Rank ${term.rank}${term.rank_title ? ` — ${term.rank_title}` : ''}` : 'No Promotion This Term'}</h2>
      <p class="phase-body" style="color:var(--text-dim);font-size:11px">Advancement roll already resolved — see the log for the result.</p>
      <p class="phase-body">Continue in this career or muster out?</p>
      ${decideActions}
    </div>
  `;
}

function renderDecideStep() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const forcedNext = character.forced_next_career_id || null;
  const forcedNextName = forcedNext ? (CAREERS.find(c => c.id === forcedNext)?.name || forcedNext) : null;

  return `
    <div class="stage-content">
      <div class="phase-label">Term ${term.overall_term_number} Complete</div>
      <h2 class="phase-title">Continue or Muster Out?</h2>
      <p class="phase-subtitle">You've survived your term. Another four years, or a new chapter?</p>
      <p class="phase-body">${term.advanced
        ? `You advanced to rank <strong>${term.rank}</strong>${term.rank_title ? ` — <strong>${term.rank_title}</strong>` : ''}.`
        : "You didn't advance this term."}</p>
      ${character.total_terms + 1 >= 4 ? `
        <p class="phase-body" style="color:var(--danger);font-style:italic">
          ⚠ Ending this next term will trigger an Aging roll. The older your Traveller, the heavier it hits.
        </p>
      ` : ''}
      ${forcedNext ? `
        <div class="event-box" style="border-color:var(--danger);margin-top:14px">
          <span class="event-label" style="color:var(--danger)">⚠ MANDATORY — ${forcedNextName.toUpperCase()}</span>
          A conviction (or equivalent) forces you into the <strong>${forcedNextName}</strong> career next term.
          You cannot muster out or continue in your current career — you must serve your sentence first.
        </div>
        <div class="phase-actions" style="margin-top:12px">
          <button class="btn danger" id="btn-enter-forced-career">SERVE YOUR SENTENCE →</button>
        </div>
      ` : `
        <div class="phase-actions">
          <button class="btn primary" id="btn-next-term">ANOTHER TERM IN ${career.name.toUpperCase()}</button>
          <button class="btn" id="btn-leave-career">MUSTER OUT OF ${career.name.toUpperCase()}</button>
        </div>
      `}
      ${anagathicsBoxHTML('btn-buy-anagathics')}
    </div>
  `;
}

// ============================================================
// PHASE 5: Mustering Out
// ============================================================

/** Build the two-row cash/benefit chart for a career's mustering-out table. */
function musterTableHTML(careerDef, termsServed, rollsUsed) {
  const table = careerDef?.mustering_out || {};
  const rolls = [1,2,3,4,5,6,7];
  const cashCells = rolls.map(n => {
    const entry = table[String(n)];
    if (!entry) return `<span class="stable-preview-cell muster-empty"><span class="stable-preview-n">${n}</span><span class="stable-preview-v">—</span></span>`;
    const raw = entry.cash;
    const label = raw != null ? (raw >= 1000 ? `Cr${(raw/1000).toFixed(0)}k` : `Cr${raw}`) : '—';
    return `<span class="stable-preview-cell"><span class="stable-preview-n">${n}</span><span class="stable-preview-v muster-cash">${escapeHTML(String(label))}</span></span>`;
  }).join('');
  const benefitCells = rolls.map(n => {
    const entry = table[String(n)];
    if (!entry) return `<span class="stable-preview-cell muster-empty"><span class="stable-preview-n">${n}</span><span class="stable-preview-v">—</span></span>`;
    const raw = entry.benefit ?? '—';
    const isStat = /^(STR|DEX|END|INT|EDU|SOC|PSI)\s*[+-]\d+$/i.test(String(raw).trim());
    return `<span class="stable-preview-cell"><span class="stable-preview-n">${n}</span><span class="stable-preview-v ${isStat ? 'is-stat' : ''}">${escapeHTML(String(raw))}</span></span>`;
  }).join('');
  const rollsLeft = termsServed != null ? (termsServed - (rollsUsed || 0)) : null;
  const rollsNote = rollsLeft != null
    ? ` · ${rollsLeft} of ${termsServed} roll${termsServed === 1 ? '' : 's'} remaining`
    : '';
  return `
    <div class="muster-table-chart">
      <div class="muster-table-label">MUSTERING-OUT TABLE · 1D ROLL${rollsNote}</div>
      <div class="muster-table-row">
        <span class="muster-col-label cash-label">CASH</span>
        <span class="stable-preview muster-preview">${cashCells}</span>
      </div>
      <div class="muster-table-row">
        <span class="muster-col-label">BENEFITS</span>
        <span class="stable-preview muster-preview">${benefitCells}</span>
      </div>
    </div>`;
}

function renderMusterPhase() {
  const careers = character.completed_careers;
  const rolls = character.pending_benefit_rolls;
  const cashRolled = character.cash_rolls_used;

  // Post-roll view: show dice readout + what was gained, then wait for "CONTINUE"
  if (uiState.lastRoll?.type === 'muster') {
    const lr = uiState.lastRoll;
    const colLabel = lr.column === 'cash' ? 'Cash Roll' : 'Benefit Roll';
    // Weapon choice: when the benefit is an unspecified "Weapon", let the player pick Melee or Firearm.
    const isWeaponChoice = lr.column !== 'cash' && (
      lr.result === 'Weapon' ||
      (typeof lr.result === 'string' && lr.result.startsWith('Weapon and'))
    );
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
      <div class="stage-content">
        <div class="phase-label">${colLabel} — ${lr.careerName || lr.careerId}</div>
        <h2 class="phase-title">${lr.column === 'cash' ? `Gained ${lr.result}` : `Benefit: ${lr.result}`}</h2>
        ${rollReadoutHTML(lr.data, { label: `${colLabel} (1D)`, showTarget: false })}
        ${isWeaponChoice ? `
          <p class="phase-body" style="margin-top:12px">Choose your weapon type:</p>
          <div class="phase-actions">
            <button class="btn primary" id="btn-weapon-melee">MELEE WEAPON →</button>
            <button class="btn primary" id="btn-weapon-firearm">FIREARM →</button>
          </div>
        ` : `
          <p class="phase-body">${lr.remaining_rolls > 0
            ? `${lr.remaining_rolls} benefit roll${lr.remaining_rolls === 1 ? '' : 's'} remaining.`
            : `All benefits claimed.`}</p>
          <div class="phase-actions">
            <button class="btn primary" id="btn-post-muster">CONTINUE →</button>
          </div>
        `}
      </div>
    `;
  }

  if (rolls === 0) {
    const pensionNote = character.pension_per_year > 0
      ? `<div style="margin-top:14px;padding:10px 14px;border:1px solid var(--amber-dim);border-radius:6px">
           <span style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">RETIREMENT PENSION</span>
           <div style="font-size:18px;font-family:var(--font-mono);color:var(--accent);margin-top:4px">
             Cr${character.pension_per_year.toLocaleString()}/year
           </div>
           <p style="font-size:11px;color:var(--text-dim);margin:4px 0 0">
             Earned after ${character.total_terms} terms of service.
           </p>
         </div>` : '';
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
      <div class="stage-content">
        <h2 class="phase-title">All Benefits Claimed</h2>
        <p class="phase-body">You've rolled all your mustering-out benefits. Your Traveller is ready.</p>
        ${pensionNote}
        <div class="phase-actions" style="margin-top:16px">
          <button class="btn primary" id="btn-finalize">FINALIZE CHARACTER →</button>
        </div>
      </div>
    `;
  }

  const careerPicker = careers.map(c => {
    const careerDef = CAREERS.find(x => x.id === c.career_id);
    const hasTable = careerDef?.mustering_out && Object.keys(careerDef.mustering_out).length > 0;
    const rollsUsed = c.benefit_rolls_used || 0;
    const maxRolls = c.benefit_rolls_earned || c.terms_served;  // earned includes rank bonus; fall back to terms for old saves
    const rollsLeft = maxRolls - rollsUsed;
    const rankBonus = maxRolls - c.terms_served;
    const exhausted = rollsLeft <= 0;
    const locked = !hasTable || exhausted;
    const rollsDesc = rankBonus > 0
      ? `${c.terms_served} terms + ${rankBonus} rank bonus = ${maxRolls} total`
      : `${c.terms_served} term${c.terms_served === 1 ? '' : 's'}`;
    return `
      <button class="card ${locked ? 'locked' : ''}" data-muster-career="${c.career_id}" ${locked ? 'disabled' : ''}>
        <div class="card-title">${careerDef?.name || c.career_id}</div>
        <div class="card-meta">${c.terms_served} TERMS · RANK ${c.final_rank} · ${exhausted ? 'NO ROLLS LEFT' : `${rollsLeft} ROLL${rollsLeft === 1 ? '' : 'S'} LEFT`}</div>
        <div class="card-desc">${!hasTable ? 'Mustering-out table not yet encoded for this career.' : exhausted ? 'All benefit rolls used.' : `${rollsLeft} of ${maxRolls} rolls remaining (${rollsDesc}).`}</div>
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
    <div class="stage-content">
      <div class="phase-label">${rolls} Benefit Rolls Remaining · ${cashRolled}/3 Cash Rolls Used</div>
      <h2 class="phase-title">Muster Out</h2>
      <p class="phase-subtitle">Time to collect your severance. Credits, gear, contacts, maybe a ship.</p>

      <p class="phase-body">You have <strong>${rolls}</strong> benefit roll${rolls === 1 ? '' : 's'} to spend. For each, choose a career to roll against, then pick the Cash column or the Benefits column. You can only use the Cash column 3 times total across all careers.</p>

      <h3 style="margin-top:20px;font-family:var(--font-mono);font-size:11px;letter-spacing:0.3em;color:var(--amber-dim);text-transform:uppercase">Pick Career</h3>
      <div class="card-grid">${careerPicker}</div>

      ${uiState.selectedCareer ? (() => {
        const selDef = CAREERS.find(x => x.id === uiState.selectedCareer);
        const selRec = careers.find(x => x.career_id === uiState.selectedCareer);
        const selMaxRolls = selRec ? (selRec.benefit_rolls_earned || selRec.terms_served) : 0;
        const selRollsLeft = selMaxRolls - (selRec?.benefit_rolls_used || 0);
        return `
          ${musterTableHTML(selDef, selMaxRolls, selRec?.benefit_rolls_used || 0)}
          ${(character.good_fortune_benefit_dm || 0) > 0 ? `
            <div class="dm-applied-box" style="margin-top:12px">
              <span class="event-label">Good Fortune</span>
              <div class="dm-chip applied">DM+2 token available — click to toggle for your next benefit roll</div>
              <label style="display:flex;align-items:center;gap:8px;margin-top:6px;cursor:pointer">
                <input type="checkbox" id="chk-good-fortune" ${uiState.useGoodFortune ? 'checked' : ''} />
                <span style="font-family:var(--font-mono);font-size:11px;color:var(--amber)">Apply Good Fortune (+2) to next benefit roll</span>
              </label>
            </div>
          ` : ''}
          <div class="phase-actions">
            <button class="btn primary" id="btn-roll-cash" ${cashRolled >= 3 || selRollsLeft <= 0 ? 'disabled' : ''}>ROLL CASH (1D)${cashRolled >= 3 ? ' — MAX' : ''}</button>
            <button class="btn" id="btn-roll-benefit" ${selRollsLeft <= 0 ? 'disabled' : ''}>ROLL BENEFIT (1D)${uiState.useGoodFortune ? ' +GOOD FORTUNE' : ''}</button>
          </div>`;
      })() : ''}
    </div>
  `;
}

function wireMusterPhase() {
  document.querySelectorAll('[data-muster-career]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedCareer = card.dataset.musterCareer;
      renderStage();
    });
  });
  const chkGoodFortune = document.getElementById('chk-good-fortune');
  if (chkGoodFortune) chkGoodFortune.addEventListener('change', () => {
    uiState.useGoodFortune = chkGoodFortune.checked;
    renderStage();
  });
  const btnCash = document.getElementById('btn-roll-cash');
  if (btnCash) {
    btnCash.addEventListener('click', async () => {
      try {
        const careerId = uiState.selectedCareer;
        const careerDef = CAREERS.find(x => x.id === careerId);
        const response = await apiCall('/api/character/muster-out',
          { career_id: careerId, column: 'cash' });
        await applyResponse(response);
        // Auto-clear selection if this career has no rolls left after the roll
        const updatedRec = character.completed_careers?.find(x => x.career_id === careerId);
        const updatedRollsLeft = updatedRec ? (updatedRec.terms_served - (updatedRec.benefit_rolls_used || 0)) : 0;
        if (updatedRollsLeft <= 0) uiState.selectedCareer = null;
        uiState.lastRoll = {
          type: 'muster',
          column: 'cash',
          data: response.roll,
          result: response.result,
          remaining_rolls: response.remaining_rolls,
          careerId,
          careerName: careerDef?.name || careerId,
        };
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
  const btnBenefit = document.getElementById('btn-roll-benefit');
  if (btnBenefit) {
    btnBenefit.addEventListener('click', async () => {
      try {
        const careerId = uiState.selectedCareer;
        const careerDef = CAREERS.find(x => x.id === careerId);
        const useGoodFortune = !!(uiState.useGoodFortune && character.good_fortune_benefit_dm > 0);
        const response = await apiCall('/api/character/muster-out',
          { career_id: careerId, column: 'benefit', use_good_fortune: useGoodFortune });
        await applyResponse(response);
        uiState.useGoodFortune = false;
        // Auto-clear selection if this career has no rolls left after the roll
        const updatedRec = character.completed_careers?.find(x => x.career_id === careerId);
        const updatedRollsLeft = updatedRec ? (updatedRec.terms_served - (updatedRec.benefit_rolls_used || 0)) : 0;
        if (updatedRollsLeft <= 0) uiState.selectedCareer = null;
        uiState.lastRoll = {
          type: 'muster',
          column: 'benefit',
          data: response.roll,
          result: response.result,
          remaining_rolls: response.remaining_rolls,
          good_fortune_used: response.good_fortune_used,
          careerId,
          careerName: careerDef?.name || careerId,
        };
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
  const btnPostMuster = document.getElementById('btn-post-muster');
  if (btnPostMuster) {
    btnPostMuster.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.selectedCareer = null;
      renderStage();
    });
  }

  // Weapon type choice — shown when a plain "Weapon" benefit is rolled
  const btnWeaponMelee = document.getElementById('btn-weapon-melee');
  if (btnWeaponMelee) {
    btnWeaponMelee.addEventListener('click', () => {
      // Find and rename the generic "Weapon" equipment entry the backend just added
      const eq = character.equipment.find(e => e.name === 'Weapon' && e.notes === 'From mustering out');
      if (eq) { eq.name = 'Melee Weapon (of choice)'; eq.notes = 'From mustering out — player picks specific blade/bludgeon'; }
      saveCharacter();
      uiState.lastRoll = null;
      renderAll();
    });
  }
  const btnWeaponFirearm = document.getElementById('btn-weapon-firearm');
  if (btnWeaponFirearm) {
    btnWeaponFirearm.addEventListener('click', () => {
      const eq = character.equipment.find(e => e.name === 'Weapon' && e.notes === 'From mustering out');
      if (eq) { eq.name = 'Firearm (of choice)'; eq.notes = 'From mustering out — player picks specific firearm'; }
      saveCharacter();
      uiState.lastRoll = null;
      renderAll();
    });
  }
  const btnFinalize = document.getElementById('btn-finalize');
  if (btnFinalize) {
    btnFinalize.addEventListener('click', () => {
      if (!uiState.skillPackageApplied) {
        character.phase = 'skill_package';
      } else {
        character.phase = 'done';
      }
      saveCharacter();
      renderAll();
    });
  }
}

// ============================================================
// PHASE 5b: Skill Package Selection
// ============================================================

function renderSkillPackagePhase() {
  const packages = Object.entries(SKILL_PACKAGES);
  const cards = packages.map(([id, pkg]) => {
    const skillList = (pkg.skills || []).join(', ');
    return `
      <button class="card" data-package-id="${escapeHTML(id)}">
        <div class="card-title">${escapeHTML(pkg.name || id)}</div>
        <div class="card-desc" style="margin-bottom:6px">${escapeHTML(pkg.description || '')}</div>
        <div style="font-family:var(--font-mono);font-size:10px;color:var(--amber-dim)">${escapeHTML(skillList)}</div>
      </button>
    `;
  }).join('');

  return `
    <div class="panel-header"><span class="led"></span><span>SKILL PACKAGE</span></div>
    <div class="stage-content">
      <div class="phase-label">Optional · MgT2e p.42</div>
      <h2 class="phase-title">Choose a Skill Package</h2>
      <p class="phase-subtitle">Before your Traveller takes to the stars, select one skill package that reflects the kind of campaign you'll be playing. Each skill is granted at level 1 (or +1 if you already have it).</p>
      <div class="card-grid">${cards}</div>
      <div class="phase-actions" style="margin-top:16px">
        <button class="btn ghost" id="btn-skip-skill-package">SKIP — NO PACKAGE →</button>
      </div>
    </div>
  `;
}

function wireSkillPackagePhase() {
  document.querySelectorAll('[data-package-id]').forEach(card => {
    card.addEventListener('click', async () => {
      const packageId = card.dataset.packageId;
      try {
        const response = await apiCall('/api/character/apply-skill-package', { package_id: packageId });
        await applyResponse(response);
        uiState.skillPackageApplied = true;
        character.phase = 'done';
        saveCharacter();
        renderAll();
      } catch (e) {
        alert(e.message || 'Could not apply skill package.');
      }
    });
  });

  const btnSkip = document.getElementById('btn-skip-skill-package');
  if (btnSkip) {
    btnSkip.addEventListener('click', () => {
      uiState.skillPackageApplied = true;
      character.phase = 'done';
      saveCharacter();
      renderAll();
    });
  }
}

// ============================================================
// PHASE 6: Done
// ============================================================

function renderDonePhase() {
  const existingConns = (character.associates || []).filter(a => (a.description || '').startsWith('Connection: '));

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 06 — READY FOR ADVENTURE</span></div>
    <div class="stage-content">
      <div class="phase-label">Character Complete · Age ${character.age} · ${character.total_terms} Terms</div>
      <h2 class="phase-title">Your Traveller Is Ready</h2>
      <p class="phase-subtitle">${escapeHTML(character.name || 'This Traveller')} has survived creation. Take the character sheet and meet your group at the starport.</p>

      <div class="phase-body">
        <p>Your character's full history is in the Mission Log. Export the JSON to save them, or import a different Traveller to continue work.</p>
      </div>

      <div class="done-card">
        <h3 class="done-card-title">Career Narrative</h3>
        <p class="empty" style="margin-bottom:10px">A full narrative record of your Traveller's career history — what they did each term, what happened, and what they returned with.</p>
        ${uiState.lastCapsule ? `
          <div class="capsule-box">${uiState.lastCapsule.split('\n\n').map(p => `<p style="margin:0 0 0.75em">${escapeHTML(p)}</p>`).join('')}</div>
          <div class="phase-actions" style="gap:6px;margin-top:6px">
            <button class="btn ghost" id="btn-regen-capsule">REGENERATE</button>
            <button class="btn ghost" id="btn-copy-capsule">COPY TEXT</button>
          </div>
        ` : `
          <div class="phase-actions">
            <button class="btn" id="btn-gen-capsule">GENERATE NARRATIVE</button>
          </div>
        `}
      </div>

      <div class="done-card">
        <h3 class="done-card-title">Connections</h3>
        <p class="empty" style="margin-bottom:10px">Link this Traveller to another PC or NPC from the group. Each connection can grant +1 in any skill, per GM approval.</p>
        ${existingConns.length ? `
          <ul class="connection-list">
            ${existingConns.map(c => `<li>${escapeHTML(c.description.replace(/^Connection: /, ''))}</li>`).join('')}
          </ul>
        ` : ''}
        <div class="connection-form">
          <input type="text" id="conn-desc" placeholder="e.g. Khadi Voss, my old Scout-Service buddy" />
          <input type="text" id="conn-skill" placeholder="Skill to bump (optional): e.g. Deception" />
          <button class="btn ghost" id="btn-add-connection">ADD CONNECTION</button>
        </div>
      </div>

      ${renderPsionicsCard()}

      <div class="phase-actions">
        <button class="btn primary" id="btn-export-pdf">⬇ EXPORT PDF</button>
        <button class="btn ghost" id="btn-export-prominent">EXPORT JSON</button>
        <button class="btn" id="btn-back-careers">← BACK TO CAREERS</button>
      </div>
    </div>
  `;
}

// Psionics is optional and GM-approved — only visible once the Traveller
// reaches the finalize/done phase. Player can decline, test, and if the
// Psi score is positive, train each of the five core talents.
function renderPsionicsCard() {
  if (!uiState.gmMode && !character.psi_tested && !uiState.psionicsOpen) {
    return `
      <div class="done-card">
        <h3 class="done-card-title">Psionics <span class="empty" style="font-weight:normal">(optional)</span></h3>
        <p class="empty" style="margin-bottom:10px">Psionic testing is normally restricted — ask your Referee before opening this panel.</p>
        <div class="phase-actions">
          <button class="btn ghost" id="btn-open-psionics">OPEN PSIONICS PANEL</button>
        </div>
      </div>
    `;
  }

  const testedHTML = character.psi_tested ? (
    character.psi > 0 ? `
      <div class="psi-result pass">
        <strong>Psi ${character.psi}</strong>
        <span class="empty">— psionic ability confirmed</span>
      </div>
    ` : `
      <div class="psi-result fail">
        <strong>No psionic potential.</strong>
        <span class="empty">The test came back flat. There is no talent to train.</span>
      </div>
    `
  ) : '';

  const talentsHTML = (character.psi > 0) ? `
    <div class="psi-talents">
      ${['telepathy','clairvoyance','telekinesis','awareness','teleportation'].map(id => {
        const trained = (character.psi_trained_talents || []).includes(id);
        const label = id.charAt(0).toUpperCase() + id.slice(1);
        return `
          <button class="btn ${trained ? 'ghost' : ''}" data-talent="${id}" ${trained ? 'disabled' : ''}>
            ${trained ? '✓ ' : ''}${label}${trained ? '' : ' — Cr200k'}
          </button>
        `;
      }).join('')}
    </div>
  ` : '';

  return `
    <div class="done-card">
      <h3 class="done-card-title">Psionics</h3>
      <p class="empty" style="margin-bottom:10px">Psionic potential test (2D 9+, DM-1 per term). On success, Psi = 2D – terms. Each talent trained costs Cr200,000 and rolls against Psi.</p>
      ${testedHTML}
      ${!character.psi_tested ? `
        <div class="phase-actions">
          <button class="btn" id="btn-test-psionics">TEST FOR POTENTIAL</button>
        </div>
      ` : ''}
      ${talentsHTML}
    </div>
  `;
}

function wireDonePhase() {
  const btnExport = document.getElementById('btn-export-prominent');
  if (btnExport) btnExport.addEventListener('click', exportCharacter);

  const btnPdf = document.getElementById('btn-export-pdf');
  if (btnPdf) btnPdf.addEventListener('click', exportPDF);
  const btnBack = document.getElementById('btn-back-careers');
  if (btnBack) btnBack.addEventListener('click', () => {
    character.phase = 'career';
    saveCharacter();
    renderAll();
  });

  const generateCapsule = async () => {
    try {
      const response = await apiCall('/api/character/capsule');
      uiState.lastCapsule = response.capsule;
      // Persist capsule on the character for export
      character.capsule_description = response.capsule;
      saveCharacter();
    } catch (e) { alert(e.message); }
    renderAll();
  };

  const btnGen = document.getElementById('btn-gen-capsule');
  if (btnGen) btnGen.addEventListener('click', generateCapsule);
  const btnRegen = document.getElementById('btn-regen-capsule');
  if (btnRegen) btnRegen.addEventListener('click', generateCapsule);
  const btnCopy = document.getElementById('btn-copy-capsule');
  if (btnCopy) btnCopy.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(uiState.lastCapsule || '');
      btnCopy.textContent = 'COPIED';
      setTimeout(() => { btnCopy.textContent = 'COPY'; }, 1200);
    } catch (e) { alert('Copy failed: ' + e.message); }
  });

  const btnAddConn = document.getElementById('btn-add-connection');
  if (btnAddConn) btnAddConn.addEventListener('click', async () => {
    const descEl = document.getElementById('conn-desc');
    const skillEl = document.getElementById('conn-skill');
    const desc = (descEl?.value || '').trim();
    const skill = (skillEl?.value || '').trim() || null;
    if (!desc) { alert('Enter a connection description first.'); return; }
    try {
      const response = await apiCall('/api/character/connection', { description: desc, skill });
      await applyResponse(response);
      if (descEl) descEl.value = '';
      if (skillEl) skillEl.value = '';
    } catch (e) { alert(e.message); }
    renderAll();
  });

  // Psionics
  const btnOpenPsi = document.getElementById('btn-open-psionics');
  if (btnOpenPsi) btnOpenPsi.addEventListener('click', () => {
    uiState.psionicsOpen = true;
    renderAll();
  });

  const btnTestPsi = document.getElementById('btn-test-psionics');
  if (btnTestPsi) btnTestPsi.addEventListener('click', async () => {
    if (!confirm('Test for psionic potential? Your Referee must approve this in most campaigns.')) return;
    try {
      const response = await apiCall('/api/character/psionics/test');
      await applyResponse(response);
    } catch (e) { alert(e.message); }
    renderAll();
  });

  document.querySelectorAll('[data-talent]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const talent = btn.dataset.talent;
      try {
        const response = await apiCall('/api/character/psionics/train', { talent_id: talent });
        await applyResponse(response);
      } catch (e) { alert(e.message); }
      renderAll();
    });
  });
}

// ============================================================
// Death overlay
// ============================================================

function renderDeadStage() {
  return `
    <div class="panel-header"><span class="led" style="background:var(--danger);box-shadow:0 0 6px var(--danger)"></span><span>DECEASED</span></div>
    <div class="stage-content">
      <div class="death-banner">
        <h2>TRAVELLER EXPIRED</h2>
        <p>${escapeHTML(character.death_reason || 'Unknown cause.')}</p>
      </div>
      <p class="phase-body">Welcome to Traveller. Your character died during creation — it happens. RAW allows survival via medical care (spend 1D × Cr10,000 as a medical loan, permanently reduce one physical characteristic by 1). Use the <strong>CHEAT DEATH</strong> button below, or start over.</p>
      <div class="phase-actions">
        <button class="btn danger" id="btn-cheat-death">CHEAT DEATH (1D × Cr10,000 loan)</button>
        <button class="btn" id="btn-new-char">NEW CHARACTER</button>
      </div>
    </div>
  `;
}

function wireDeadStage() {
  document.getElementById('btn-new-char').addEventListener('click', () => {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
    window.location.replace(window.location.pathname);
  });

  const btnCheatDeath = document.getElementById('btn-cheat-death');
  if (btnCheatDeath) {
    btnCheatDeath.addEventListener('click', async () => {
      try {
        const resp = await apiCall('/api/character/cheat-death', {});
        await applyResponse(resp);
        // Show which stat was reduced and cost incurred
        alert(`Survived! Medical loan: Cr${resp.cost.toLocaleString()}. ${resp.stat_reduced} reduced by 1. Character revived and returning to career phase.`);
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  }
}

// ============================================================
// Export / Import / Reset
// ============================================================

function exportCharacter() {
  const blob = new Blob([JSON.stringify(character, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${(character.name || 'traveller').replace(/\s+/g, '_')}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function exportPDF() {
  const btn = document.getElementById('btn-export-pdf');
  if (btn) { btn.textContent = 'GENERATING…'; btn.disabled = true; }
  try {
    const res = await fetch('/api/character/export-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ character }),
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(character.name || 'traveller').replace(/\s+/g, '_')}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('PDF export failed: ' + e.message);
  } finally {
    if (btn) { btn.textContent = '⬇ EXPORT PDF'; btn.disabled = false; }
  }
}

async function importCharacter(file) {
  const text = await file.text();
  try {
    const imported = JSON.parse(text);
    character = imported;
    saveCharacter();
    renderAll();
  } catch (e) {
    alert('Invalid character JSON: ' + e.message);
  }
}

// ============================================================
// Initial render
// ============================================================

function renderGMPanel() {
  const panel = document.getElementById('gm-panel');
  if (!panel) return;
  panel.style.display = uiState.gmMode ? 'block' : 'none';
  if (!uiState.gmMode) return;
  const lastEl = document.getElementById('gm-last-rolls');
  if (lastEl) {
    const rolls = uiState.gmLastRolls;
    lastEl.textContent = rolls?.length
      ? `Last sent: [${rolls.join(', ')}]`
      : '';
  }
}

// ============================================================
// Mobile tab navigation
// ============================================================

const MOBILE_PANELS = { sheet: 'sheet', stage: 'stage', log: 'log-panel' };

function setMobileTab(tab) {
  uiState.mobileTab = tab;
  // Update panel visibility
  Object.entries(MOBILE_PANELS).forEach(([key, id]) => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('mobile-panel-active', key === tab);
  });
  // Update tab button active state
  document.querySelectorAll('.mobile-tab').forEach(btn => {
    btn.classList.toggle('mobile-tab-active', btn.dataset.tab === tab);
  });
}

function wireMobileTabs() {
  document.querySelectorAll('.mobile-tab').forEach(btn => {
    btn.addEventListener('click', () => setMobileTab(btn.dataset.tab));
  });
  // Apply default tab on load
  setMobileTab(uiState.mobileTab || 'stage');
}

function renderAll() {
  renderSheet();
  renderStage();
  renderLog();
  renderGMPanel();
  // Re-apply mobile tab visibility after every render (innerHTML wipes classes)
  setMobileTab(uiState.mobileTab || 'stage');
}

async function bootstrap() {
  const hasSaved = loadCharacter();
  if (!hasSaved || !character) {
    await freshCharacter();
  }

  try {
    const res = await fetch('/api/careers/full');
    if (res.ok) {
      const data = await res.json();
      CAREER_DATA = data.careers || {};
    }
  } catch (e) { /* network error — picker will degrade gracefully */ }

  try {
    const pkgRes = await fetch('/api/skill-packages');
    if (pkgRes.ok) {
      const pkgData = await pkgRes.json();
      SKILL_PACKAGES = pkgData.packages || {};
    }
  } catch (e) { /* non-fatal */ }

  // Apply saved theme before first paint
  if (uiState.themeLight) document.body.classList.add('theme-light');

  // Mobile tab bar wiring
  wireMobileTabs();

  renderAll();

  document.getElementById('btn-export').addEventListener('click', exportCharacter);
  document.getElementById('import-file').addEventListener('change', (e) => {
    if (e.target.files[0]) importCharacter(e.target.files[0]);
  });

  document.getElementById('btn-reset').addEventListener('click', () => {
    if (!confirm('Start a new character? This will wipe the current character and log.')) return;
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
    window.location.replace(window.location.pathname);
  });

  document.getElementById('btn-make-npc').addEventListener('click', async () => {
    if (!confirm('Generate a complete NPC? This will replace the current character.')) return;
    const btn = document.getElementById('btn-make-npc');
    btn.textContent = 'GENERATING…';
    btn.disabled = true;
    try {
      const res = await fetch('/api/character/generate-npc');
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      character = data.character;
      saveCharacter();
      renderAll();
    } catch (e) {
      alert('NPC generation failed: ' + e.message);
    } finally {
      btn.textContent = 'MAKE NPC';
      btn.disabled = false;
    }
  });

  // Theme toggle
  const btnTheme = document.getElementById('btn-theme-toggle');
  if (btnTheme) {
    const applyTheme = () => {
      document.body.classList.toggle('theme-light', !!uiState.themeLight);
      btnTheme.textContent = uiState.themeLight ? '◑' : '◐';
      btnTheme.title = uiState.themeLight ? 'Switch to dark theme' : 'Switch to light theme';
    };
    applyTheme();
    btnTheme.addEventListener('click', () => {
      uiState.themeLight = !uiState.themeLight;
      try { localStorage.setItem('theme', uiState.themeLight ? 'light' : 'dark'); } catch (e) { /* ignore */ }
      applyTheme();
    });
  }

  // Font-size cycle: normal → large → xl → normal
  const btnFontSize = document.getElementById('btn-font-size');
  if (btnFontSize) {
    const FONT_LEVELS = ['normal', 'large', 'xl'];
    const FONT_LABELS = { normal: 'Aa', large: 'A+', xl: 'A++' };
    const FONT_TITLES = { normal: 'Font: Normal — click for Large', large: 'Font: Large — click for Extra Large', xl: 'Font: Extra Large — click for Normal' };
    const savedFont = localStorage.getItem('traveller_font_size') || 'normal';
    let currentFont = FONT_LEVELS.includes(savedFont) ? savedFont : 'normal';
    const applyFont = () => {
      document.body.classList.remove('font-large', 'font-xl');
      if (currentFont !== 'normal') document.body.classList.add(`font-${currentFont}`);
      btnFontSize.textContent = FONT_LABELS[currentFont];
      btnFontSize.title = FONT_TITLES[currentFont];
    };
    applyFont();
    btnFontSize.addEventListener('click', () => {
      const idx = FONT_LEVELS.indexOf(currentFont);
      currentFont = FONT_LEVELS[(idx + 1) % FONT_LEVELS.length];
      try { localStorage.setItem('traveller_font_size', currentFont); } catch (e) { /* ignore */ }
      applyFont();
    });
  }

  const btnGm = document.getElementById('btn-gm-mode');
  if (btnGm) {
    const paintGm = () => {
      btnGm.classList.toggle('active', !!uiState.gmMode);
      btnGm.textContent = uiState.gmMode ? 'GM ●' : 'GM';
      document.body.classList.toggle('gm-mode', !!uiState.gmMode);
      renderGMPanel();
    };
    paintGm();
    btnGm.addEventListener('click', () => {
      uiState.gmMode = !uiState.gmMode;
      uiState.gmLastRolls = [];
      try { localStorage.setItem('traveller_gm_mode', uiState.gmMode ? '1' : '0'); } catch (e) { /* ignore */ }
      paintGm();
    });
  }

  const fairBtn = document.getElementById('btn-fair-use');
  const fairModal = document.getElementById('fair-use-modal');
  const fairClose = document.getElementById('btn-close-fair-use');
  if (fairBtn && fairModal) {
    fairBtn.addEventListener('click', () => { fairModal.hidden = false; });
  }
  if (fairClose && fairModal) {
    fairClose.addEventListener('click', () => { fairModal.hidden = true; });
    fairModal.addEventListener('click', (e) => {
      if (e.target === fairModal) fairModal.hidden = true;
    });
  }
}

bootstrap();
