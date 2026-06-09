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

// D66 Solomani Contacts, Allies, Rivals and Enemies table
// (Aliens of Charted Space Vol.1 / Solomani Rim sourcebook)
const _SOL_CONTACTS = {
  11: 'Alien Ambassador or Trade Delegate',
  12: 'Army Officer, Solomani Confederation',
  13: 'Artist or Performer',
  14: 'Colonist or Farmer',
  15: 'Confederation Ministry Bureaucrat',
  16: 'Conspirator or Terrorist',
  21: 'Corporate Executive',
  22: 'Corporate or Foreign Agent',
  23: 'Criminal',
  24: 'Crusading Journalist',
  25: 'Diplomat from Foreign Ministry',
  26: 'Dissident',
  31: 'Entrepreneur',
  32: 'Explorer',
  33: 'Free Trader',
  34: 'Inveterate Gambler',
  35: 'Marine, Confederation Navy',
  36: 'Navy Officer, Solomani Confederation',
  41: 'Physician',
  42: 'Planetary Solomani Party Official',
  43: 'Police Officer',
  44: 'Prindig Worker',
  45: 'Private Investigator',
  46: 'Racist Thug',
  51: 'Religious Leader',
  52: 'Researcher',
  53: 'Retired Confederation Navy Admiral',
  54: 'Scientist',
  55: 'Secretariat Delegate',
  56: 'Smuggler',
  61: 'Solomani Party Militant',
  62: 'SolSec Field Agent',
  63: 'SolSec Monitor or Secret Agent',
  64: 'Starport Administrator',
  65: 'Tourist',
  66: 'Uplifted Dolphin or Ape',
};

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

// ============================================================
// ROBOT BUILDER — rules data + calculation engine
// ============================================================

const ROBOT_RULES = {
  chassis: [
    { id:"size-1", size:1, name:"Size 1", slots:1, hits:1, attackDm:-4, equivalent:"Rat", basicCost:100, traits:["Small (-4)"] },
    { id:"size-2", size:2, name:"Size 2", slots:2, hits:4, attackDm:-3, equivalent:"Cat", basicCost:200, traits:["Small (-3)"] },
    { id:"size-3", size:3, name:"Size 3", slots:4, hits:8, attackDm:-2, equivalent:"Dog", basicCost:400, traits:["Small (-2)"] },
    { id:"size-4", size:4, name:"Size 4", slots:8, hits:12, attackDm:-1, equivalent:"Bwap/Droyne/Goat", basicCost:800, traits:["Small (-1)"] },
    { id:"size-5", size:5, name:"Size 5", slots:16, hits:20, attackDm:0, equivalent:"Human/Vargr", basicCost:1000, traits:[] },
    { id:"size-6", size:6, name:"Size 6", slots:32, hits:32, attackDm:1, equivalent:"Aslan/Cow", basicCost:2000, traits:["Large (+1)"] },
    { id:"size-7", size:7, name:"Size 7", slots:64, hits:50, attackDm:2, equivalent:"K'kree/Bear", basicCost:4000, traits:["Large (+2)"] },
    { id:"size-8", size:8, name:"Size 8", slots:128, hits:72, attackDm:3, equivalent:"Virushi/Rhino", basicCost:8000, traits:["Large (+3)"] }
  ],
  locomotion: [
    { id:"none", name:"None (Stationary)", minTl:5, agility:null, traits:[], endurance:216, multiplier:1, notes:"Adds 25% available slots." },
    { id:"wheels", name:"Wheels", minTl:5, agility:0, traits:[], endurance:72, multiplier:2, notes:"Prepared surface movement." },
    { id:"wheels-atv", name:"Wheels, ATV", minTl:5, agility:0, traits:["ATV"], endurance:72, multiplier:3, notes:"Rough-terrain wheel movement." },
    { id:"tracks", name:"Tracks", minTl:5, agility:-1, traits:["ATV"], endurance:72, multiplier:2, notes:"Rugged tracked movement." },
    { id:"grav", name:"Grav", minTl:9, agility:1, traits:["Flyer (Idle)"], endurance:24, multiplier:20, notes:"Flying grav locomotion." },
    { id:"aeroplane", name:"Aeroplane", minTl:5, agility:1, traits:["Flyer (Idle)"], endurance:12, multiplier:12, notes:"Requires runway." },
    { id:"aquatic", name:"Aquatic", minTl:6, agility:-2, traits:["Seafarer"], endurance:72, multiplier:4, notes:"Liquid surface movement." },
    { id:"vtol", name:"VTOL", minTl:7, agility:0, traits:["Flyer (Idle)"], endurance:24, multiplier:14, notes:"Vertical take-off flight." },
    { id:"walker", name:"Walker", minTl:8, agility:0, traits:["ATV"], endurance:72, multiplier:10, notes:"Legged movement." },
    { id:"hovercraft", name:"Hovercraft", minTl:7, agility:1, traits:["ACV"], endurance:24, multiplier:10, notes:"Air cushion movement." },
    { id:"thruster", name:"Thruster", minTl:7, agility:1, traits:[], endurance:2, multiplier:20, notes:"Secondary locomotion; 0.1G." }
  ],
  brains: [
    { id:"primitive-7",    family:"Primitive",     name:"Primitive TL7",       minTl:7,  computer:0,  cost:10000,   intelligence:1,  skillDm:-2, capabilities:["Programmable"] },
    { id:"primitive-8",    family:"Primitive",     name:"Primitive TL8+",      minTl:8,  computer:0,  cost:100,     intelligence:1,  skillDm:-2, capabilities:["Programmable"] },
    { id:"basic-8",        family:"Basic",         name:"Basic TL8",           minTl:8,  computer:1,  cost:20000,   intelligence:3,  skillDm:-1, capabilities:["Limited language","Security/0"] },
    { id:"hunter-8",       family:"Hunter/Killer", name:"Hunter/Killer TL8",   minTl:8,  computer:1,  cost:30000,   intelligence:3,  skillDm:-1, capabilities:["Limited Friend or Foe","Security/1","Recon/0"] },
    { id:"basic-10",       family:"Basic",         name:"Basic TL10+",         minTl:10, computer:1,  cost:4000,    intelligence:4,  skillDm:-1, capabilities:["Limited language","Security/0"] },
    { id:"hunter-10",      family:"Hunter/Killer", name:"Hunter/Killer TL10+", minTl:10, computer:1,  cost:6000,    intelligence:4,  skillDm:-1, capabilities:["Limited Friend or Foe","Security/1","Recon/0"] },
    { id:"advanced-10",    family:"Advanced",      name:"Advanced TL10",       minTl:10, computer:2,  cost:100000,  intelligence:6,  skillDm:0,  capabilities:["Intelligent Interface","Expert/1","Security/1"] },
    { id:"advanced-11",    family:"Advanced",      name:"Advanced TL11",       minTl:11, computer:2,  cost:50000,   intelligence:7,  skillDm:0,  capabilities:["Intelligent Interface","Expert/1","Security/1"] },
    { id:"advanced-12",    family:"Advanced",      name:"Advanced TL12+",      minTl:12, computer:2,  cost:10000,   intelligence:8,  skillDm:0,  capabilities:["Intelligent Interface","Expert/1","Security/1"] },
    { id:"very-advanced-12",family:"Very Advanced",name:"Very Advanced TL12",  minTl:12, computer:3,  cost:500000,  intelligence:9,  skillDm:1,  capabilities:["Intellect Interface","Expert/2","Security/2"] },
    { id:"very-advanced-13",family:"Very Advanced",name:"Very Advanced TL13",  minTl:13, computer:4,  cost:500000,  intelligence:10, skillDm:1,  capabilities:["Intellect Interface","Expert/2","Security/2"] },
    { id:"very-advanced-14",family:"Very Advanced",name:"Very Advanced TL14+", minTl:14, computer:5,  cost:500000,  intelligence:11, skillDm:1,  capabilities:["Intellect Interface","Expert/2","Security/2"] },
    { id:"self-aware-15",  family:"Self-Aware",    name:"Self-Aware TL15",     minTl:15, computer:10, cost:1000000, intelligence:12, skillDm:2,  capabilities:["Near sentient","Expert/3","Security/3"] },
    { id:"self-aware-16",  family:"Self-Aware",    name:"Self-Aware TL16+",    minTl:16, computer:15, cost:1000000, intelligence:13, skillDm:2,  capabilities:["Near sentient","Expert/3","Security/3"] },
    { id:"conscious-17",   family:"Conscious",     name:"Conscious TL17",      minTl:17, computer:20, cost:5000000, intelligence:15, skillDm:3,  capabilities:["Conscious Intelligence","Security/3"] },
    { id:"conscious-18",   family:"Conscious",     name:"Conscious TL18+",     minTl:18, computer:30, cost:1000000, intelligence:15, skillDm:3,  capabilities:["Conscious Intelligence","Security/3"] }
  ],
  bandwidthUpgrades: [
    { id:"bw-basic-1",  name:"Basic/H-K +1",        minTl:8,  bandwidth:1,  slots:1, cost:5000    },
    { id:"bw-adv-2",    name:"Advanced TL10 +2",     minTl:10, bandwidth:2,  slots:1, cost:5000    },
    { id:"bw-adv-3",    name:"Advanced TL11 +3",     minTl:11, bandwidth:3,  slots:1, cost:10000   },
    { id:"bw-adv-4",    name:"Advanced TL12 +4",     minTl:12, bandwidth:4,  slots:1, cost:20000   },
    { id:"bw-va-6",     name:"Very Advanced +6",     minTl:12, bandwidth:6,  slots:1, cost:50000   },
    { id:"bw-va-8",     name:"Very Advanced +8",     minTl:12, bandwidth:8,  slots:1, cost:100000  },
    { id:"bw-sa-10",    name:"Self-Aware +10",       minTl:15, bandwidth:10, slots:1, cost:500000  },
    { id:"bw-sa-15",    name:"Self-Aware +15",       minTl:15, bandwidth:15, slots:1, cost:1000000 },
    { id:"bw-sa-20",    name:"Self-Aware +20",       minTl:15, bandwidth:20, slots:1, cost:2500000 },
    { id:"bw-con-30",   name:"Conscious TL17 +30",   minTl:17, bandwidth:30, slots:1, cost:5000000 },
    { id:"bw-con-40",   name:"Conscious TL17 +40",   minTl:17, bandwidth:40, slots:1, cost:10000000 },
    { id:"bw-con-50",   name:"Conscious TL18 +50",   minTl:18, bandwidth:50, slots:1, cost:5000000 }
  ],
  armorByTl: [
    { minTl:6,  maxTl:8,  baseProtection:2, maxProtection:20, slotPercent:0.010, maxPerSlot:1, costPerSlot:250  },
    { minTl:9,  maxTl:11, baseProtection:3, maxProtection:30, slotPercent:0.005, maxPerSlot:2, costPerSlot:1000 },
    { minTl:12, maxTl:14, baseProtection:4, maxProtection:40, slotPercent:0.004, maxPerSlot:3, costPerSlot:1500 },
    { minTl:15, maxTl:17, baseProtection:4, maxProtection:50, slotPercent:0.003, maxPerSlot:4, costPerSlot:2500 },
    { minTl:18, maxTl:99, baseProtection:5, maxProtection:60, slotPercent:0.0025,maxPerSlot:5, costPerSlot:5000 }
  ],
  systems: [
    { id:"visual",     name:"Visual Spectrum Sensor",   slots:0, cost:0,     bandwidth:0, notes:"Default suite item." },
    { id:"voder",      name:"Voder Speaker",             slots:0, cost:0,     bandwidth:0, notes:"Default suite item." },
    { id:"auditory",   name:"Auditory Sensor",           slots:0, cost:0,     bandwidth:0, notes:"Default suite item." },
    { id:"wireless",   name:"Wireless Data Link",        slots:0, cost:0,     bandwidth:0, notes:"Default suite item." },
    { id:"transceiver",name:"Transceiver, 5km",          slots:0, cost:0,     bandwidth:0, notes:"Default suite item." },
    { id:"pris",       name:"PRIS Sensor",               minTl:12, slots:0, cost:2000,  bandwidth:0, traits:["IR/UV Vision"], notes:"IR/UV visual sensor." },
    { id:"thermal",    name:"Thermal Sensor",            minTl:6,  slots:0, cost:500,   bandwidth:0, traits:["IR Vision"], notes:"Infrared thermal vision." },
    { id:"env-processor",name:"Environment Processor",  minTl:10, slots:0, cost:10000, bandwidth:0, traits:["Heightened Senses"], notes:"Sensor processor + Recon 0." },
    { id:"vacuum-protection",name:"Vacuum Protection",  minTl:7,  slots:0, costPerBaseSlot:600,  bandwidth:0, notes:"Includes hostile environment." },
    { id:"hostile-protection",name:"Hostile Env Protection", minTl:6, slots:0, costPerBaseSlot:300, bandwidth:0, notes:"Hostile atmosphere/temp." },
    { id:"reflec",     name:"Reflec Armour",             minTl:10, slots:0, costPerBaseSlot:100,  bandwidth:0, traits:["Reflec"], notes:"+10 vs laser; conflicts with camo." },
    { id:"gecko",      name:"Gecko Grippers",            minTl:9,  slots:0, costPerBaseSlot:500,  bandwidth:0, notes:"Wall/ceiling adhesion." },
    { id:"magnetic",   name:"Magnetic Grippers",         minTl:8,  slots:0, costPerBaseSlot:10,   bandwidth:0, notes:"Adheres to metallic surfaces." },
    { id:"encryption", name:"Encryption Module",         minTl:6,  slots:0, cost:4000,  bandwidth:0, notes:"Hardens comms and data." },
    { id:"drone-interface",name:"Drone Interface",       minTl:6,  slots:0, cost:100,   bandwidth:0, notes:"Remote control interface." },
    { id:"atmospheric-sensor",name:"Atmospheric Sensor",minTl:8,  slots:0, cost:100,   bandwidth:0, notes:"Pressure/composition data." },
    { id:"auditory-broad",name:"Auditory Sensor, Broad",minTl:8,  slots:0, cost:200,   bandwidth:0, traits:["Heightened Senses"], notes:"Broad frequency audio." },
    { id:"geiger",     name:"Geiger Counter",            minTl:8,  slots:0, cost:400,   bandwidth:0, notes:"Radiation detection." },
    { id:"light-intensifier-basic",name:"Light Intensifier, Basic",minTl:7,slots:0,cost:500,bandwidth:0,notes:"Low-light mono vision." },
    { id:"light-intensifier-advanced",name:"Light Intensifier, Adv",minTl:9,slots:0,cost:1250,bandwidth:0,traits:["IR Vision"],notes:"Light amp + thermal." },
    { id:"olfactory-basic",name:"Olfactory Sensor, Basic",minTl:8,slots:0,cost:1000,bandwidth:0,notes:"Generalised smell." },
    { id:"olfactory-improved",name:"Olfactory Sensor, Imp",minTl:10,slots:0,cost:3500,bandwidth:0,traits:["Heightened Senses"],notes:"Improved olfactory." },
    { id:"tightbeam",  name:"Tightbeam Communicator",   minTl:8,  slots:1, cost:2000,  bandwidth:0, notes:"LoS 5,000km laser comm." },
    { id:"satellite-uplink",name:"Satellite Uplink",    minTl:6,  slots:2, cost:1000,  bandwidth:0, notes:"Satellite/ship comms." },
    { id:"active-camouflage",name:"Active Camouflage",  minTl:15, slots:1, costPerBaseSlot:10000,bandwidth:0,traits:["Invisible","Stealth 4"],notes:"DM-4 to Recon/sensors." },
    { id:"corrosive-protection",name:"Corrosive Env Protection",minTl:9,slots:1,costPerBaseSlot:600,bandwidth:0,notes:"Corrosive atmosphere prot." },
    { id:"radiation-protection",name:"Radiation Env Protection",minTl:7,slots:1,costPerBaseSlot:600,bandwidth:0,notes:"+50×TL rads protection." },
    { id:"self-repairing",name:"Self-Repairing Chassis",minTl:11,slotsPercent:0.05,costPerBaseSlot:1000,bandwidth:0,notes:"Repairs minor damage." },
    { id:"quick-charger",name:"Quick Charger",          minTl:8,  slots:1, cost:200,   bandwidth:0, notes:"Full recharge in 1 hour." },
    { id:"recon-sensor-basic",name:"Recon Sensor, Basic",minTl:7,slots:2,cost:1000,bandwidth:0,notes:"Recon 1 from sensors." },
    { id:"recon-sensor-improved",name:"Recon Sensor, Imp",minTl:8,slots:1,cost:100,bandwidth:0,notes:"Recon 1 from sensors." },
    { id:"recon-sensor-enhanced",name:"Recon Sensor, Enh",minTl:10,slots:1,cost:10000,bandwidth:0,notes:"Recon 2 from sensors." },
    { id:"recon-sensor-advanced",name:"Recon Sensor, Adv",minTl:12,slots:1,cost:20000,bandwidth:0,notes:"Recon 3 from sensors." },
    { id:"small-weapon-mount",name:"Weapon Mount, Small",minTl:5,slots:1,cost:500,bandwidth:0,notes:"Pistol/melee/grenade." },
    { id:"medium-weapon-mount",name:"Weapon Mount, Medium",minTl:5,slots:2,cost:1000,bandwidth:0,notes:"Rifle/larger melee." },
    { id:"heavy-weapon-mount",name:"Weapon Mount, Heavy",minTl:5,slots:10,cost:5000,bandwidth:0,notes:"Portable heavy weapons." },
    { id:"toolkit",    name:"Specialised Toolkit",      slots:1, cost:5000,  bandwidth:0, notes:"Tool set for a specific task." },
    { id:"medikit",    name:"Medikit",                  slots:1, cost:5000,  bandwidth:0, notes:"Medical hardware." },
    { id:"fire-control-basic",name:"Fire Control, Basic",minTl:6,slots:1,cost:1000,bandwidth:0,notes:"Basic targeting system." }
  ],
  skills: [
    { name:"Admin",       minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Advocate",    minTl:10, bandwidth:0, baseCost:500  },
    { name:"Animals",     minTl:9,  bandwidth:0, baseCost:200  },
    { name:"Art",         minTl:10, bandwidth:0, baseCost:500  },
    { name:"Astrogation", minTl:12, bandwidth:1, baseCost:500  },
    { name:"Athletics",   minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Broker",      minTl:10, bandwidth:0, baseCost:200  },
    { name:"Carouse",     minTl:11, bandwidth:1, baseCost:500  },
    { name:"Deception",   minTl:13, bandwidth:1, baseCost:1000 },
    { name:"Diplomat",    minTl:10, bandwidth:1, baseCost:500  },
    { name:"Drive",       minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Electronics", minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Engineer",    minTl:9,  bandwidth:0, baseCost:200  },
    { name:"Explosives",  minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Flyer",       minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Gun Combat",  minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Gunner",      minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Heavy Weapons",minTl:8, bandwidth:0, baseCost:100  },
    { name:"Investigate", minTl:11, bandwidth:1, baseCost:500  },
    { name:"Language",    minTl:9,  bandwidth:0, baseCost:200  },
    { name:"Leadership",  minTl:13, bandwidth:1, baseCost:1000 },
    { name:"Mechanic",    minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Medic",       minTl:9,  bandwidth:0, baseCost:200  },
    { name:"Melee",       minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Navigation",  minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Persuade",    minTl:11, bandwidth:1, baseCost:500  },
    { name:"Pilot",       minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Recon",       minTl:10, bandwidth:0, baseCost:500  },
    { name:"Science",     minTl:9,  bandwidth:0, baseCost:200  },
    { name:"Seafarer",    minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Stealth",     minTl:10, bandwidth:0, baseCost:500  },
    { name:"Steward",     minTl:8,  bandwidth:0, baseCost:100  },
    { name:"Streetwise",  minTl:13, bandwidth:1, baseCost:1000 },
    { name:"Survival",    minTl:10, bandwidth:0, baseCost:200  },
    { name:"Tactics",     minTl:8,  bandwidth:0, baseCost:100  }
  ]
};

const ROBOT_DEFAULT_CONFIG = {
  name: "New Robot", purpose: "", techLevel: 12, notes: "",
  chassisId: "size-5", brainId: "advanced-12", locomotionId: "walker",
  bandwidthUpgradeId: "",
  frameMods:    { armorAdded:0, reduceProtection:false, efficiency:false, powerPacks:0, resilientHits:0, lightHits:0 },
  brainMods:    { intBoost:0, hardened:false },
  mobilityMods: { agilityBoost:0, speedMod:0, vehicleSpeed:false, vehicleSpeedBoosts:0, secondaryLocomotionId:"" },
  manipulators: [],
  systems: ["visual","voder","auditory","wireless","transceiver"],
  customOptions: [],
  weapons: [],
  skills: [{ name:"Recon", level:1 }],
  finalCost: { percent:0, flat:0 }
};

// ── robot helpers ──────────────────────────────────────────────
function rbFindRule(list, id) { return list.find(x => x.id === id); }
function rbN(v, fb=0) { const n=Number(v); return Number.isFinite(n)?n:fb; }
function rbClamp(v,mn,mx) { return Math.max(mn, Math.min(mx, rbN(v))); }
function rbFmtCr(v) { return `Cr ${Math.round(v||0).toLocaleString()}`; }

function robotNormalize(c) {
  if (!c) c = {};
  const d = ROBOT_DEFAULT_CONFIG;
  const n = { ...structuredClone(d), ...c,
    frameMods:    { ...d.frameMods,    ...(c.frameMods    || {}) },
    brainMods:    { ...d.brainMods,    ...(c.brainMods    || {}) },
    mobilityMods: { ...d.mobilityMods, ...(c.mobilityMods || {}) },
    finalCost:    { ...d.finalCost,    ...(c.finalCost    || {}) }
  };
  if (!rbFindRule(ROBOT_RULES.chassis, n.chassisId)) n.chassisId = d.chassisId;
  if (!rbFindRule(ROBOT_RULES.brains, n.brainId)) n.brainId = d.brainId;
  if (!rbFindRule(ROBOT_RULES.locomotion, n.locomotionId)) n.locomotionId = d.locomotionId;
  n.frameMods.armorAdded     = rbClamp(n.frameMods.armorAdded, 0, 60);
  n.frameMods.powerPacks     = rbClamp(n.frameMods.powerPacks, 0, 3);
  n.frameMods.resilientHits  = Math.max(0, rbN(n.frameMods.resilientHits));
  n.frameMods.lightHits      = Math.max(0, rbN(n.frameMods.lightHits));
  n.brainMods.intBoost       = rbClamp(n.brainMods.intBoost, 0, 3);
  n.mobilityMods.agilityBoost= rbClamp(n.mobilityMods.agilityBoost, 0, 4);
  n.mobilityMods.speedMod    = rbClamp(n.mobilityMods.speedMod, -12, 12);
  n.mobilityMods.vehicleSpeedBoosts = rbClamp(n.mobilityMods.vehicleSpeedBoosts, 0, 3);
  n.manipulators = (n.manipulators||[]).map(m=>({
    size:  Math.max(1, rbN(m.size, 5)),
    count: Math.max(1, rbN(m.count, 1)),
    strBoost: Math.max(0, rbN(m.strBoost)),
    dexBoost: Math.max(0, rbN(m.dexBoost))
  }));
  n.systems = (n.systems||[]).filter(id => rbFindRule(ROBOT_RULES.systems, id));
  n.customOptions = (n.customOptions||[]).map(o=>({
    name: o.name||"Custom Option", minTl: Math.max(0,rbN(o.minTl)),
    slots: Math.max(0,rbN(o.slots)), cost: rbN(o.cost), traits: o.traits||"", notes: o.notes||""
  }));
  n.weapons = (n.weapons||[]).map(w=>({
    name: w.name||"Weapon", mount: w.mount||"small",
    slots: Math.max(0,rbN(w.slots,1)), cost: rbN(w.cost), traits: w.traits||""
  }));
  n.skills = (n.skills||[]).map(s=>({
    name: ROBOT_RULES.skills.find(x=>x.name===s.name)?.name || d.skills[0].name,
    level: rbClamp(s.level, 0, 4),
    specialty: s.specialty || ''
  }));
  return n;
}

function robotArmorRow(tl) {
  return ROBOT_RULES.armorByTl.find(r=>tl>=r.minTl&&tl<=r.maxTl) || ROBOT_RULES.armorByTl[0];
}
function robotSlotsFromPct(chassis, pct) {
  if (!chassis||pct<=0) return 0;
  return Math.max(1, Math.ceil(chassis.slots*pct));
}
function robotBrainSlotCost(chassis, brain, tl) {
  if (!chassis||!brain||brain.computer===0) return 0;
  const free = Math.max(1, brain.computer - Math.max(0, tl - brain.minTl));
  return chassis.size >= free ? 0 : 1;
}
function robotManipSlots(chassis, mSize) {
  if (!chassis) return 0;
  const diff = mSize - chassis.size;
  const ratio = diff>=2?0.4:diff===1?0.2:diff===0?0.1:diff===-1?0.05:diff===-2?0.02:0.01;
  return Math.max(1, Math.ceil(chassis.slots*ratio));
}
function robotManipStats(tl, size, strBoost=0, dexBoost=0) {
  const baseStr=(2*size)-1, baseDex=Math.ceil(tl/2+1);
  return { baseStr, baseDex, str:baseStr+strBoost, dex:baseDex+dexBoost,
           maxStr:baseStr*2, maxDex:tl+3 };
}
function robotIntUpgrade(brain, bwUpgrade, intBoost) {
  if (!brain||intBoost<=0) return {boost:0,bandwidth:0,cost:0,finalInt:brain?.intelligence||0,overCapacity:false};
  const bandwidth=intBoost*(intBoost+1)/2;
  const finalInt=brain.intelligence+intBoost;
  let cost=1;
  for (let s=brain.intelligence+1;s<=finalInt;s++) cost*=s;
  cost*=1000;
  if (finalInt>=12) cost*=2;
  const totalBW=(brain.computer||0)+(bwUpgrade?.bandwidth||0);
  return {boost:intBoost,bandwidth,cost,finalInt,overCapacity:bandwidth>totalBW};
}
function robotSysCost(system, chassis) {
  if (Number.isFinite(system.costPerBaseSlot)) return system.costPerBaseSlot*(chassis?.slots||0);
  return system.cost||0;
}
function robotSysSlots(system, chassis) {
  if (Number.isFinite(system.slotsPercent)) return robotSlotsFromPct(chassis,system.slotsPercent);
  return system.slots||0;
}

function calculateRobotConfig(cfg) {
  const tl = rbN(cfg.techLevel, 12);
  const chassis    = rbFindRule(ROBOT_RULES.chassis, cfg.chassisId);
  const brain      = rbFindRule(ROBOT_RULES.brains,  cfg.brainId);
  const locomotion = rbFindRule(ROBOT_RULES.locomotion, cfg.locomotionId);
  const bwUpgrade  = rbFindRule(ROBOT_RULES.bandwidthUpgrades, cfg.bandwidthUpgradeId);
  const secLoco    = rbFindRule(ROBOT_RULES.locomotion, cfg.mobilityMods?.secondaryLocomotionId);
  const armor      = robotArmorRow(tl);
  const baseChassisCost = (chassis?.basicCost||0)*(locomotion?.multiplier||1);

  const addedProt  = rbN(cfg.frameMods?.armorAdded);
  const armorSlots = addedProt>0
    ? Math.max(Math.ceil((chassis?.slots||0)*armor.slotPercent*addedProt), Math.ceil(addedProt/armor.maxPerSlot), 1) : 0;
  const armorCost  = armorSlots*armor.costPerSlot;
  const protection = armor.baseProtection-(cfg.frameMods?.reduceProtection?1:0)+addedProt;
  const ppSlots    = robotSlotsFromPct(chassis,0.1)*rbN(cfg.frameMods?.powerPacks);
  const ppCost     = ppSlots*500;
  const resSlots   = rbN(cfg.frameMods?.resilientHits);
  const resCost    = resSlots*baseChassisCost*0.05;
  const lightHits  = rbN(cfg.frameMods?.lightHits);
  const lightSave  = lightHits*50*(locomotion?.multiplier||1);
  const protSave   = cfg.frameMods?.reduceProtection ? baseChassisCost*0.1 : 0;
  const effCost    = cfg.frameMods?.efficiency ? baseChassisCost*0.5 : 0;

  const agilBoost  = rbN(cfg.mobilityMods?.agilityBoost);
  const speedMod   = rbN(cfg.mobilityMods?.speedMod);
  const vsbBoosts  = rbN(cfg.mobilityMods?.vehicleSpeedBoosts);
  const agilCost   = baseChassisCost*[0,1,2,4,8][agilBoost];
  const speedCost  = baseChassisCost*0.1*speedMod;
  const vsbSlots   = cfg.mobilityMods?.vehicleSpeed ? robotSlotsFromPct(chassis,0.25)+(robotSlotsFromPct(chassis,0.1)*vsbBoosts) : 0;
  const vsbCost    = cfg.mobilityMods?.vehicleSpeed ? baseChassisCost*(2**vsbBoosts) : 0;
  const secSlots   = secLoco ? robotSlotsFromPct(chassis,0.25) : 0;
  const secCost    = secLoco ? secSlots*500*secLoco.multiplier : 0;

  const brainCost  = brain?.cost||0;
  const bwCost     = bwUpgrade?.cost||0;
  const intellect  = robotIntUpgrade(brain, bwUpgrade, rbN(cfg.brainMods?.intBoost));
  const hardCost   = cfg.brainMods?.hardened ? (brainCost+bwCost)*0.5 : 0;

  const manipulators=(cfg.manipulators||[]).map(m=>{
    const sz=rbN(m.size,chassis?.size||1), cnt=rbN(m.count,1),
          sb=rbN(m.strBoost), db=rbN(m.dexBoost);
    const stats=robotManipStats(tl,sz,sb,db);
    const mslots=robotManipSlots(chassis,sz)*cnt;
    return {...m,...stats,size:sz,count:cnt,strBoost:sb,dexBoost:db,slots:mslots,
            cost:100*sz*cnt+100*sz*(sb**2)*cnt+200*sz*(db**2)*cnt};
  });

  const systems=(cfg.systems||[]).map(id=>rbFindRule(ROBOT_RULES.systems,id)).filter(Boolean).map(s=>({
    ...s, calcSlots:robotSysSlots(s,chassis), calcCost:robotSysCost(s,chassis) }));
  const customOpts=(cfg.customOptions||[]).map(o=>({...o,calcSlots:rbN(o.slots),calcCost:rbN(o.cost)}));
  const weapons=(cfg.weapons||[]).map(w=>({...w,calcSlots:rbN(w.slots),calcCost:rbN(w.cost)}));
  const skills=(cfg.skills||[]).map(entry=>{
    const sk=ROBOT_RULES.skills.find(s=>s.name===entry.name)||ROBOT_RULES.skills[0];
    const lv=rbN(entry.level);
    return {...entry,skillDef:sk,level:lv,cost:sk.baseCost*(10**lv),bandwidth:sk.bandwidth+lv,minTl:sk.minTl+lv};
  });

  const availSlots=(chassis?.slots||0)+(locomotion?.id==="none"?Math.ceil((chassis?.slots||0)*0.25):0);
  const usedSlots=
    robotBrainSlotCost(chassis,brain,tl)+(bwUpgrade?.slots||0)+armorSlots+ppSlots+resSlots+vsbSlots+secSlots+
    manipulators.reduce((s,m)=>s+m.slots,0)+
    systems.reduce((s,x)=>s+x.calcSlots,0)+
    customOpts.reduce((s,o)=>s+o.calcSlots,0)+
    weapons.reduce((s,w)=>s+w.calcSlots,0);
  const usedBW=intellect.bandwidth+systems.reduce((s,x)=>s+(x.bandwidth||0),0)+skills.reduce((s,sk)=>s+sk.bandwidth,0);

  let endurance=locomotion?.endurance||0;
  if (tl>=15) endurance*=2; else if (tl>=12) endurance*=1.5;
  if (cfg.frameMods?.efficiency) endurance*=2;
  endurance*=(1+rbN(cfg.frameMods?.powerPacks));
  endurance*=speedMod>=0?Math.max(0,1-(speedMod*0.1)):1+(Math.abs(speedMod)*0.1);

  const agility=(locomotion?.agility||0)+agilBoost;
  const tacticalSpeed=Math.max(0,5+(locomotion?.agility||0)+agilBoost+speedMod);

  const preFinalCost=baseChassisCost+brainCost+bwCost+intellect.cost+hardCost+
    armorCost+effCost+ppCost+resCost-lightSave-protSave+agilCost+speedCost+vsbCost+secCost+
    manipulators.reduce((s,m)=>s+m.cost,0)+systems.reduce((s,x)=>s+x.calcCost,0)+
    customOpts.reduce((s,o)=>s+o.calcCost,0)+weapons.reduce((s,w)=>s+w.calcCost,0)+
    skills.reduce((s,sk)=>s+sk.cost,0);
  const finalCost=Math.max(0,(preFinalCost*(1+rbN(cfg.finalCost?.percent)/100))+rbN(cfg.finalCost?.flat));

  const traits=[...(chassis?.traits||[]),...(locomotion?.traits||[]),...(secLoco?.traits||[]),
    ...(protection>0?[`Armour (+${protection})`]:[]),...(cfg.brainMods?.hardened?["Hardened"]:[]),
    ...systems.flatMap(x=>x.traits||[])];

  return { chassis, brain, locomotion, secLoco, bwUpgrade, baseChassisCost,
    armor:{...armor,addedProt,armorSlots,armorCost,protection},
    intellect, manipulators, systems, customOpts, weapons, skills,
    slots:{used:usedSlots,total:availSlots},
    bandwidth:{used:usedBW,total:(brain?.computer||0)+(bwUpgrade?.bandwidth||0),inherent:brain?.computer||0},
    cost:finalCost,
    hits:(chassis?.hits||0)+resSlots-lightHits,
    endurance:Math.round(endurance), agility, tacticalSpeed,
    traits:[...new Set(traits)] };
}

function validateRobotConfig(cfg, calc) {
  const msgs=[];
  msgs.push(calc.slots.used>calc.slots.total
    ?{type:"error",text:`Slots exceeded by ${calc.slots.used-calc.slots.total}.`}
    :{type:"ok",text:`${calc.slots.total-calc.slots.used} slots remaining.`});
  msgs.push(calc.bandwidth.used>calc.bandwidth.total
    ?{type:"error",text:`Bandwidth exceeded by ${calc.bandwidth.used-calc.bandwidth.total}.`}
    :{type:"ok",text:`${calc.bandwidth.total-calc.bandwidth.used} bandwidth remaining.`});
  if (calc.hits<=0) msgs.push({type:"error",text:"Hits must remain above 0."});
  if (calc.intellect.overCapacity) msgs.push({type:"error",text:"INT upgrade needs more bandwidth than brain has."});
  if (!cfg.name?.trim()) msgs.push({type:"warn",text:"Give the robot a name before finalizing."});
  return msgs;
}

// Derive Foundry-compatible characteristic object from a robot calc result
function robotFoundryChars(cfg, calc) {
  const firstM=calc.manipulators[0]||{
    str:((calc.chassis?.size||5)*2)-1,
    dex:Math.ceil((rbN(cfg.techLevel,12)/2)+1)
  };
  const vals={
    STR:Math.max(0,Math.round(firstM.str||0)),
    DEX:Math.max(0,Math.round((firstM.dex||0)+calc.agility)),
    END:Math.max(0,Math.round(calc.hits||0)),
    INT:Math.max(0,Math.round(calc.intellect.finalInt||0)),
    EDU:Math.max(0,Math.round(calc.bandwidth.total||0)),
    SOC:0
  };
  return vals;
}

// Create a FoundryVTT actor JSON from a robot character (client-side)
function createRobotFoundryExport(cfg) {
  cfg = robotNormalize(cfg);
  const calc = calculateRobotConfig(cfg);
  const tl = rbN(cfg.techLevel, 12);

  function rbFoundryId(seed) {
    const src=`${seed}-${Date.now()}-${Math.random()}`;
    let h=0;
    for (let i=0;i<src.length;i++) { h=((h<<5)-h)+src.charCodeAt(i); h|=0; }
    return `${Math.abs(h).toString(16)}${Math.random().toString(16).slice(2)}`.slice(0,16).padEnd(16,"0");
  }
  function rbItem(name,notes,cost=0) {
    const now=Date.now();
    return {name,type:"item",system:{tl,weight:0,cost:Math.round(cost||0),notes:notes||"",active:false,quantity:1,status:"carried",legality:9,description:notes||""},
      _id:rbFoundryId(name),img:"systems/mgt2e/icons/items/item.svg",effects:[],folder:null,sort:0,flags:{},
      _stats:{compendiumSource:null,duplicateSource:null,exportSource:null,coreVersion:"13.351",systemId:"mgt2e",systemVersion:"0.21.0.0",lastModifiedBy:null,createdTime:now,modifiedTime:now},
      ownership:{default:0}};
  }

  const chars=robotFoundryChars(cfg,calc);
  const itemRows=[
    rbItem(calc.chassis?.name||"Robot Chassis",`Size ${calc.chassis?.size||"?"}; ${calc.chassis?.slots||0} slots; base hits ${calc.chassis?.hits||0}.`,calc.baseChassisCost),
    rbItem(calc.brain?.name||"Robot Brain",`${calc.brain?.capabilities?.join(", ")||""}; Computer/${calc.brain?.computer??0}; INT ${calc.intellect.finalInt}.`,(calc.brain?.cost||0)+calc.intellect.cost),
    rbItem(calc.locomotion?.name||"Locomotion",`${calc.locomotion?.notes||""}; endurance ${calc.endurance} hours.`,0),
    rbItem("Robot Armour",`Protection +${calc.armor.protection}; ${calc.armor.armorSlots} slots.`,calc.armor.armorCost)
  ];
  calc.manipulators.forEach(m=>itemRows.push(rbItem(`${m.count}×Size ${m.size} Manipulator`,`STR ${m.str}; DEX ${m.dex}; slots ${m.slots}.`,m.cost)));
  calc.systems.forEach(s=>itemRows.push(rbItem(s.name,`${s.notes||""}. Slots ${s.calcSlots}.`,s.calcCost)));
  calc.customOpts.forEach(o=>itemRows.push(rbItem(o.name,`${o.notes||""}. Slots ${o.calcSlots}.`,o.calcCost)));
  calc.weapons.forEach(w=>itemRows.push(rbItem(w.name,`${w.mount} mount. Slots ${w.calcSlots}.`,w.calcCost)));

  // Build skills in the same nested format the server-side character export uses:
  //   parent key (e.g. "gunner") → { id, value, trained, specialities: { turret: { id, value } } }
  // This is what MGT2e Foundry expects — NOT a flat "gunnerturret" key with a speciality string.
  const _rbSkillIdMap = {
    'gun combat':'guncombat','guncombat':'guncombat',
    'gunner':'gunner',
    'heavy weapons':'heavyweapons','heavyweapons':'heavyweapons',
    'tactics':'tactics','drive':'drive','electronics':'electronics',
    'engineer':'engineer','flyer':'flyer','pilot':'pilot',
    'melee':'melee','athletics':'athletics','recon':'recon',
    'stealth':'stealth','survival':'survival','medic':'medic',
    'mechanic':'mechanic','science':'science','navigate':'navigation',
    'navigation':'navigation','seafarer':'seafarer','language':'language',
    'profession':'profession','art':'art','animals':'animals',
    'admin':'admin','advocate':'advocate','astrogation':'astrogation',
    'broker':'broker','carouse':'carouse','deception':'deception',
    'diplomat':'diplomat','explosives':'explosives','gambler':'gambler',
    'investigate':'investigate','jack of all trades':'jackofalltrades',
    'leadership':'leadership','persuade':'persuade','steward':'steward',
    'streetwise':'streetwise','vacc suit':'vaccsuit','vaccsuit':'vaccsuit',
  };
  const _rbSpecIdMap = {
    // Gunner
    'turret':'turret','capital':'capital','ortillery':'ortillery','screen':'screen',
    // Gun Combat
    'energy':'energy','slug':'slug','archaic':'archaic',
    // Heavy Weapons
    'artillery':'artillery','portable':'portable','vehicle':'vehicle',
    // Tactics
    'military':'military','naval':'naval',
    // Drive
    'wheel':'wheel','track':'track','walker':'walker','hovercraft':'hovercraft','mole':'mole',
    // Electronics
    'comms':'comms','computers':'computers','remote ops':'remoteOps','sensors':'sensors',
    // Engineer
    'm-drive':'mDrive','j-drive':'jDrive','life support':'lifeSupport','power':'power',
    // Flyer
    'grav':'grav','rotor':'rotor','wing':'wing','airship':'airship','ornithopter':'ornithopter',
    // Pilot
    'small craft':'smallCraft','spacecraft':'spacecraft','capital ships':'capitalShips',
    // Melee
    'blade':'blade','bludgeon':'bludgeon','unarmed':'unarmed','natural':'natural',
    // Athletics
    'strength':'strength','dexterity':'dexterity','endurance':'endurance',
    // Science
    'robotics':'robotics','cybernetics':'cybernetics','physics':'physics',
    'biology':'biology','chemistry':'chemistry','astronomy':'astronomy',
    'psychology':'psychology','archaeology':'archaeology','planetology':'planetology',
    // Seafarer
    'ocean ships':'oceanShips','personal':'personal','sail':'sail','submarine':'submarine',
    // Language
    'anglic':'galanglic','galanglic':'galanglic',
  };

  // Full MGT2e skill tree — every skill the sheet must show.
  // Untrained entries appear at value 0 / trained:false so Foundry renders -3.
  const _rbAllSkillTree = {
    admin:[], advocate:[], astrogation:[], broker:[], carouse:[], deception:[],
    diplomat:[], explosives:[], gambler:[], independence:[], investigate:[],
    jackofalltrades:[], leadership:[], mechanic:[], medic:[], navigation:[],
    persuade:[], recon:[], stealth:[], steward:[], streetwise:[], survival:[], vaccsuit:[],
    animals:['handling','training','vetinary'],
    art:['holography','instrument','performer','visualMedia','write'],
    athletics:['dexterity','endurance','strength'],
    drive:['hovercraft','mole','track','walker','wheel'],
    electronics:['comms','computers','remoteOps','sensors'],
    engineer:['jDrive','lifeSupport','mDrive','power'],
    flyer:['airship','grav','ornithopter','rotor','wing'],
    guncombat:['archaic','energy','slug'],
    gunner:['capital','ortillery','screen','turret'],
    heavyweapons:['artillery','portable','vehicle'],
    language:['galanglic','gvegh','oynprith','trokh','vilani','zdetl'],
    melee:['blade','bludgeon','natural','unarmed'],
    pilot:['capitalShips','smallCraft','spacecraft'],
    profession:['belter','biologicals','civilEngineering','construction','hydroponics','polymers','robotics'],
    science:['archaeology','astronomy','biology','chemistry','cosmology','cybernetics',
             'economics','genetics','history','linquistics','philosophy','physics',
             'planetology','psionicology','psychology','sophontology','xenology'],
    seafarer:['oceanShips','personal','sail','submarine'],
    tactics:['military','naval'],
  };

  // Pre-seed every skill as untrained, then overlay robot's actual skills
  const _rbSkillWork = {};
  Object.entries(_rbAllSkillTree).forEach(([sid, specIds]) => {
    const specs = {};
    specIds.forEach(sp => { specs[sp] = { level: 0, trained: false }; });
    _rbSkillWork[sid] = { base: 0, trained: false, specs };
  });

  calc.skills.forEach(sk => {
    const sid = _rbSkillIdMap[sk.name.toLowerCase()] || sk.name.toLowerCase().replace(/[^a-z0-9]+/g,'');
    if (!_rbSkillWork[sid]) _rbSkillWork[sid] = { base: 0, trained: false, specs: {} };
    if (sk.specialty) {
      const specId = _rbSpecIdMap[sk.specialty.toLowerCase()] || sk.specialty.toLowerCase().replace(/[^a-z0-9]+/g,'');
      if (!_rbSkillWork[sid].specs[specId]) _rbSkillWork[sid].specs[specId] = { level: 0, trained: false };
      _rbSkillWork[sid].specs[specId].level = Math.max(_rbSkillWork[sid].specs[specId].level, sk.level);
      _rbSkillWork[sid].specs[specId].trained = true;
    } else {
      _rbSkillWork[sid].base = Math.max(_rbSkillWork[sid].base, sk.level);
      _rbSkillWork[sid].trained = true;
    }
  });

  const skills = {};
  Object.entries(_rbSkillWork).forEach(([sid, data]) => {
    const entry = { id: sid, value: data.base, trained: data.trained };
    if (Object.keys(data.specs).length) {
      entry.specialities = {};
      Object.entries(data.specs).forEach(([spId, spData]) => {
        entry.specialities[spId] = { id: spId, value: spData.trained && spData.level > 0 ? String(spData.level) : spData.level, trained: spData.trained };
      });
    }
    skills[sid] = entry;
  });

  const charsFull=["STR","DEX","END","INT","EDU","SOC","CHA","TER","PSI","WLT","LCK","MRL","STY","RES","FOL","REP"].reduce((a,k)=>({...a,[k]:{value:chars[k]||0,current:chars[k]||0,show:k in chars,default:false}}),{});

  return {
    name:cfg.name||"Traveller Robot", type:"traveller",
    img:"systems/mgt2e/icons/actors/traveller.svg",
    system:{
      speed:{base:calc.tacticalSpeed,value:calc.tacticalSpeed},
      initiative:{base:calc.agility,value:calc.agility},
      size:calc.chassis?.attackDm||0, rads:0, weightCarried:0, heavyLoad:50, maxLoad:100, modifiers:{},
      hits:{value:calc.hits,max:calc.hits,damage:0,tmpDamage:0},
      description:`<p>${escapeHTML(cfg.purpose||"")}</p><p>${calc.chassis?.name||""} ${calc.locomotion?.name||""} robot; Hits ${calc.hits}; Protection +${calc.armor.protection}; Speed ${calc.tacticalSpeed}m. Brain: ${calc.brain?.name||""}; INT ${calc.intellect.finalInt}. Cost: ${rbFmtCr(calc.cost)}.</p>`,
      settings:{hideUntrained:false,onlyBackground:false,resetOnRoll:false,columns:"3",lockCharacteristics:false,sortByCategory:false,lockSkills:false,autoAge:true,autoHits:true},
      characteristics:charsFull, skills, damage:{STR:{value:0},DEX:{value:0},END:{value:0,tmp:0}},
      sophont:{age:"0",species:"Robot",speciesTraits:calc.traits.join(", "),gender:"None",weight:0,height:0,profession:cfg.purpose||"Robot",homeworld:""},
      finance:{cash:"0",pension:"0",medicalDebt:"0",mortgage:"0",livingCosts:"0",otherIncome:"0",shipShares:0,description:`Construction cost: ${rbFmtCr(calc.cost)}`},
      terms:0,startAge:0,termLength:0,entryYear:1105,entryAge:0,currentYear:1105,birthYear:1105
    },
    items:itemRows, effects:[], folder:null,
    flags:{mgt2e:{}},
    prototypeToken:{name:cfg.name||"Traveller Robot",displayName:0,actorLink:true,width:1,height:1}
  };
}

// ── end robot builder engine ──────────────────────────────────

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
  'Profession':     [
    'Colonist/Farming', 'Colonist/Ranching',
    'Freeloader/Scrounging', 'Freeloader/Security',
    'Hostile Environment/Contaminant', 'Hostile Environment/High-g',
    'Hostile Environment/Low-g', 'Hostile Environment/Underwater',
    'Spacer/Belter', 'Spacer/Crewmember',
    'Sport/Various',
    'Worker/Armourer', 'Worker/Metalworking',
  ],
  'Science':        ['Archaeology', 'Astronomy', 'Biology', 'Chemistry', 'Cosmology', 'Cybernetics', 'Economics', 'Genetics', 'History', 'Linguistics', 'Philosophy', 'Physics', 'Planetology', 'Psionicology', 'Psychology', 'Robotics', 'Sophontology', 'Xenology'],
  'Seafarer':       ['Ocean Ships', 'Personal', 'Sail', 'Submarine'],
  'Tactics':        ['Military', 'Naval'],
};

const STORAGE_KEY = 'traveller-character-v1';

let SKILL_PACKAGES = {};
let BG_PACKAGES = {};      // background_packages.json — loaded async in bootstrap
let CAREER_DATA = {};      // full career JSON (loaded async in bootstrap)
let CAREER_PACKAGES = {};  // career_packages.json — loaded async in bootstrap

let character = null;
let uiState = {
  // Transient selections that aren't part of the character yet
  selectedSpecies: null,
  selectedBgSkills: new Set(),
  selectedPreCareerSkills: new Set(),
  selectedCareer: null,
  selectedMusterIndex: null,
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
  // Background package picker
  bgPackageMode: false,         // true → show package picker instead of skill chips
  selectedBgPackage: null,      // package id currently highlighted
  bgPackageSkillChoices: {},    // { skillName: chosenSpeciality }  for "any" skills
  // Career package picker
  careerPackageMode: false,     // true → show career package picker instead of career grid
  careerPackagePhase: 'picker', // 'picker' | 'finalising'
  selectedCareerPackage: null,  // package id
  careerPackageSkillChoices: {},// { key: chosenSpeciality } for "any" package skills
  careerFinalising: {           // finalising panel state
    careerChoice: null,         // 'boost_one_to_4' | 'boost_three_by_1' | 'rank_4_only'
    careerSkill: null,          // for boost_one_to_4: { name, speciality }
    career3Skills: [],          // for boost_three_by_1: [{ name, speciality }, ...]
    travellerPairId: null,      // 1-12
    travellerSpecialties: {},   // { key: specialty } for any-skills in chosen pair
    benefitId: null,            // 1-6
  },
  // Robot builder tab ('frame'|'brain'|'mobility'|'equipment'|'skills'|'finalize')
  robotTab: 'frame',
  // Optional extra characteristics panel
  extraStatsEnabled: false,
  extraStatsSelected: new Set(),   // which ids are checked
  extraStatsRolls: {},             // last roll results { PSI: {total,dice,...}, ... }
  // Mobile tab: 'sheet' | 'stage' | 'log'
  mobileTab: 'stage',
  // Theme cycle: 'dark' (amber CRT) | 'light' (green terminal) | 'mono' (clean B&W)
  theme: localStorage.getItem('theme') || 'dark',
  // Card description visibility toggle
  hideDesc: localStorage.getItem('traveller_hide_desc') === '1',
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
  // Aslan setup: intermediate roll result display (cleared when player clicks Continue)
  aslanRollResult: null,
  // Zhodani training: last talent train result (cleared when phase ends)
  zhodaniTrainResult: null,
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
  if (!res.ok) throw new Error(`Server error ${res.status} creating new character`);
  const data = await res.json();
  if (!data.character) throw new Error('Server returned no character data');
  character = data.character;
  const keepGm   = uiState.gmMode;
  const keepTheme = uiState.theme;
  const keepHideDesc = uiState.hideDesc;
  uiState = {
    selectedSpecies: null,
    selectedBgSkills: new Set(),
    selectedPreCareerSkills: new Set(),
    selectedCareer: null,
    selectedMusterIndex: null,
    selectedAssignment: null,
    selectedCoverCareer: null,
    lastRoll: null,
    swapPick: null, swapA: 'EDU', swapB: 'STR',
    subPhase: null, pendingAge: false,
    agingResult: null, agingNextAction: null, agingSelectedStats: [],
    anagathicsPhaseDone: false, pendingNextTermAction: null,
    gmMode: keepGm,
    theme: keepTheme,
    hideDesc: keepHideDesc,
    connectionsDone: false, connections: [],
    basicTrainingSkills: null,
    skillPackageApplied: false,
    extraStatsEnabled: false,
    extraStatsSelected: new Set(),
    extraStatsRolls: {},
    heroicRoll: false,
    pcSkillSpecialtyPick: null,
    pendingAdvancementSkill: false,
    lastAdvanceRoll: null,
    pendingCareerSpecialty: null,
    bgExpandedCascade: null,
    pendingSkillGrant: null,
    pendingMishapNoEject: false,
    aslanRollResult: null,
    zhodaniTrainResult: null,
    lastCapsule: null, psionicsOpen: false, gmLastRolls: [],
    mobileTab: 'stage',
  };
  saveCharacter();
}

// ------------------------------------------------------------
// Character save slots  (5 max, stored separately from active char)
// ------------------------------------------------------------

const SAVE_SLOT_PREFIX      = 'traveller-save-slot-';
const SAVE_SLOT_META_SUFFIX = '-meta';
const MAX_SAVE_SLOTS        = 5;

function _saveSlotKey(idx)     { return SAVE_SLOT_PREFIX + idx; }
function _saveSlotMetaKey(idx) { return SAVE_SLOT_PREFIX + idx + SAVE_SLOT_META_SUFFIX; }

/**
 * Returns { character, savedAt } or null.
 * The character object is the raw export-format JSON (same as EXPORT JSON).
 * Metadata (savedAt) is stored in a parallel key so the character JSON stays clean.
 */
function readSaveSlot(idx) {
  try {
    const raw = localStorage.getItem(_saveSlotKey(idx));
    if (!raw) return null;
    const charObj = JSON.parse(raw);
    let savedAt = null;
    try {
      const meta = localStorage.getItem(_saveSlotMetaKey(idx));
      if (meta) savedAt = JSON.parse(meta).savedAt || null;
    } catch (e) { /* ignore bad meta */ }
    return { character: charObj, savedAt };
  } catch (e) { return null; }
}

/**
 * Saves charObj verbatim (raw export format) into slot idx.
 * Date goes into the parallel meta key.
 */
function writeSaveSlot(idx, charObj) {
  // Store raw character — identical format to EXPORT JSON / the file the user downloads
  localStorage.setItem(_saveSlotKey(idx), JSON.stringify(charObj, null, 2));
  // Store just the timestamp separately so the slot picker can show it
  localStorage.setItem(_saveSlotMetaKey(idx), JSON.stringify({ savedAt: new Date().toISOString() }));
}

function deleteSaveSlot(idx) {
  localStorage.removeItem(_saveSlotKey(idx));
  localStorage.removeItem(_saveSlotMetaKey(idx));
}

function renderSavesModal() {
  const body = document.getElementById('saves-modal-body');
  if (!body) return;

  const fmtDate = iso => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString(undefined, { year:'numeric', month:'short', day:'numeric' })
      + ' ' + d.toLocaleTimeString(undefined, { hour:'2-digit', minute:'2-digit' });
  };

  let html = `<p class="empty" style="margin-bottom:14px">Save your current character to one of 5 slots, or load a previously saved character. Loading will replace your current character.</p>`;
  html += `<div style="display:flex;flex-direction:column;gap:10px">`;

  for (let i = 0; i < MAX_SAVE_SLOTS; i++) {
    const slot = readSaveSlot(i);
    const label = slot
      ? `<div style="font-weight:700;color:var(--accent)">${escapeHTML(slot.character.name || '(unnamed)')} · Age ${slot.character.age || 18}</div>
         <div style="font-size:11px;color:var(--text-dim)">${escapeHTML(fmtDate(slot.savedAt))} · phase: ${escapeHTML(slot.character.phase || '?')}</div>`
      : `<div style="color:var(--text-dim);font-style:italic">— empty —</div>`;

    html += `<div style="display:flex;align-items:center;gap:10px;padding:10px 12px;border:1px solid var(--border);border-radius:6px;background:rgba(255,255,255,0.02)">
      <div style="min-width:60px;font-size:11px;letter-spacing:1px;color:var(--text-dim)">SLOT ${i + 1}</div>
      <div style="flex:1">${label}</div>
      <div style="display:flex;gap:6px;flex-shrink:0">
        <button class="btn" data-save-idx="${i}" style="padding:4px 10px;font-size:11px">SAVE</button>
        <button class="btn primary" data-load-idx="${i}" style="padding:4px 10px;font-size:11px" ${slot ? '' : 'disabled'}>LOAD</button>
        <button class="btn danger" data-del-idx="${i}" style="padding:4px 10px;font-size:11px" ${slot ? '' : 'disabled'}>DEL</button>
      </div>
    </div>`;
  }

  html += `</div>`;
  body.innerHTML = html;

  // Wire buttons
  body.querySelectorAll('[data-save-idx]').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.saveIdx, 10);
      const existing = readSaveSlot(idx);
      if (existing) {
        const existName = existing.character.name || '(unnamed)';
        if (!confirm(`Overwrite slot ${idx + 1} (${existName})?`)) return;
      }
      writeSaveSlot(idx, character);
      renderSavesModal();
    });
  });

  body.querySelectorAll('[data-load-idx]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const idx = parseInt(btn.dataset.loadIdx, 10);
      const slot = readSaveSlot(idx);
      if (!slot) return;
      const slotName = slot.character.name || '(unnamed)';
      if (!confirm(`Load "${slotName}"? This will replace your current character.`)) return;
      character = slot.character;
      saveCharacter();
      // Reset transient UI state but keep theme/GM/desc
      const keepGm    = uiState.gmMode;
      const keepTheme = uiState.theme;
      const keepHideDesc2 = uiState.hideDesc;
      uiState = {
        selectedSpecies: null,
        selectedBgSkills: new Set(),
        selectedPreCareerSkills: new Set(),
        selectedCareer: null,
        selectedMusterIndex: null,
        selectedAssignment: null,
        selectedCoverCareer: null,
        lastRoll: null,
        swapPick: null, swapA: 'EDU', swapB: 'STR',
        subPhase: null, pendingAge: false,
        agingResult: null, agingNextAction: null, agingSelectedStats: [],
        anagathicsPhaseDone: false, pendingNextTermAction: null,
        gmMode: keepGm,
        theme: keepTheme,
        hideDesc: keepHideDesc2,
        connectionsDone: false, connections: [],
        basicTrainingSkills: null,
        skillPackageApplied: false,
        extraStatsEnabled: false,
        extraStatsSelected: new Set(),
        extraStatsRolls: {},
        heroicRoll: false,
        pcSkillSpecialtyPick: null,
        pendingAdvancementSkill: false,
        lastAdvanceRoll: null,
        pendingCareerSpecialty: null,
        bgExpandedCascade: null,
        pendingSkillGrant: null,
        pendingMishapNoEject: false,
        aslanRollResult: null,
        zhodaniTrainResult: null,
        lastCapsule: null, psionicsOpen: false, gmLastRolls: [],
        mobileTab: 'stage',
      };
      document.getElementById('saves-modal').hidden = true;
      renderAll();
    });
  });

  body.querySelectorAll('[data-del-idx]').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.delIdx, 10);
      const slot = readSaveSlot(idx);
      if (!slot) return;
      const delName = slot.character.name || '(unnamed)';
      if (!confirm(`Delete slot ${idx + 1} (${delName})?`)) return;
      deleteSaveSlot(idx);
      renderSavesModal();
    });
  });
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
  // Characteristic Modifiers table, extended above 15 (18-20 -> +4, 21-23 -> +5,
  // +1 per +3 thereafter). (score / 3 floored) - 2 reproduces the whole table.
  if (score == null || isNaN(score) || score <= 0) return -3;
  return Math.floor(score / 3) - 2;
}

function formatDM(dm) {
  if (dm > 0) return `+${dm}`;
  return `${dm}`;
}

// Return the display label for the SOC characteristic for a given character.
// Returns 'RES' (Hiver), 'CHA' (Vargr), null (Droyne — no SOC), or 'SOC'.
// Checks species_id first (set after apply_species); falls back to society_id
// for single-species societies so the rolling phase shows the right label too.
function socLabelForChar(char) {
  const spId = char && char.species_id;
  if (spId) {
    const sp = SPECIES.find(s => s.id === spId);
    if (sp) {
      if (sp.res_replaces_soc) return 'RES';
      if (sp.uses_cha) return 'CHA';
      if (sp.no_soc) return null;
    }
  }
  // Pre-species fallback: infer from society for single-species societies
  const socId = char && char.society_id;
  if (socId === 'vargr_extents') return 'CHA';
  if (socId === 'droyne_oytrip') return null;
  return 'SOC';
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

  const _socLabel = socLabelForChar(character);
  const statCells = ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC']
    .filter(stat => stat !== 'SOC' || _socLabel !== null)
    .map((stat) => {
      const val = stats[stat];
      const dm = charDM(val);
      const label = stat === 'SOC' ? _socLabel : stat;
      return `
        <div class="stat-cell">
          <span class="stat-label">${label}</span>
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
      ` : '')
    + (character.reputation > 0 ? `
        <div class="stat-cell stat-cell-rep">
          <span class="stat-label">REP</span>
          <span class="stat-value">${character.reputation}</span>
          <span class="stat-dm">DM ${formatDM(charDM(character.reputation))}</span>
        </div>
      ` : '');

  const skillsList = character.skills.length
    ? character.skills.map((s) => {
        const label = s.speciality ? `${s.name} (${s.speciality})` : s.name;
        return `<li><span>${label}</span><span class="skill-level">${s.level}</span></li>`;
      }).join('')
    : '<li class="empty">No skills yet</li>';

  const equipList = character.equipment.length
    ? character.equipment.map((e) => {
        const protTag = e.protection != null ? ` <span class="tag tag-armor">Protection +${e.protection}</span>` : '';
        const noteTag = e.notes ? ` <span class="empty">— ${escapeHTML(e.notes)}</span>` : '';
        return `<li>${escapeHTML(e.name)}${protTag}${noteTag}</li>`;
      }).join('')
    : '<li class="empty">No equipment</li>';

  const traits = (character.traits || []);
  const traitsHTML = traits.length
    ? `<ul class="traits-list">${traits.map(t => `<li><strong>${esc(t.name)}:</strong> ${esc(t.description)}</li>`).join('')}</ul>`
    : '<p class="empty">No species traits</p>';
  const _spForNotes = SPECIES.find(s => s.id === character.species_id);
  const speciesNotesHTML = (_spForNotes && _spForNotes.species_notes && _spForNotes.species_notes.length)
    ? `<ul class="species-notes-list">${_spForNotes.species_notes.map(n => `<li>${esc(n)}</li>`).join('')}</ul>`
    : '';

  const careersHTML = character.completed_careers.length
    ? `<ul class="skill-list">${character.completed_careers.map(c => {
        const careerDef = CAREERS.find(x => x.id === c.career_id);
        const asgnName = careerDef?.assignments?.[c.assignment_id]?.name || c.assignment_id;
        const rankStr = c.final_rank_title || (c.final_rank > 0 ? `Rank ${c.final_rank}` : 'No rank');
        return `<li><span>${careerDef?.name || c.career_id} — ${asgnName}</span><span class="skill-level">${c.terms_served}t</span></li><li style="border:none;padding:0 0 4px 8px;color:var(--muted);font-size:10px">${rankStr}, ${c.left_due_to}</li>`;
      }).join('')}</ul>`
    : '<p class="empty">No careers yet</p>';

  const associates = character.associates || [];
  // "wife" associates are shown in the K'kree Family section, not the standard Associates panel.
  const buckets = { contact: [], ally: [], rival: [], enemy: [] };
  associates.forEach((a, i) => {
    if (a.kind !== 'wife' && buckets[a.kind]) buckets[a.kind].push({ a, i });
  });
  const bucketOrder = [
    ['contact', 'Contacts'],
    ['ally', 'Allies'],
    ['rival', 'Rivals'],
    ['enemy', 'Enemies'],
  ];
  const nonWifeAssociates = associates.filter(a => a.kind !== 'wife');
  const associatesHTML = nonWifeAssociates.length
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
      }).join('') || '<p class="empty">No associates yet</p>'
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
          <span>SPECIES<br><strong>${esc(species.name)}</strong></span>
          <span>AGE<br><strong>${character.age}</strong></span>
          <span>TERMS<br><strong>${character.total_terms}</strong></span>
          <span>CREDITS<br><strong>Cr${character.credits.toLocaleString()}</strong></span>
          ${character.gender ? `<span>GENDER<br><strong>${character.gender === 'male' ? '♂ Male' : '♀ Female'}</strong></span>` : ''}
          ${(character.aslan_setup_status && character.aslan_setup_status.rite_score != null && character.aslan_setup_status.phase === 'done') ? `<span title="Aslan Rite of Passage Score — used as DM for career qualification">RITE<br><strong>${character.aslan_setup_status.rite_score}</strong></span>` : ''}
          ${(() => { const t = nobleTitle(character.species_id, character.characteristics?.SOC); return t ? `<span class="noble-title-badge" title="Imperial Noble Title">TITLE<br><strong>${t}</strong></span>` : ''; })()}
          ${(() => {
            if (character.species_id !== 'zhodani') return '';
            const soc = character.characteristics?.SOC ?? 0;
            const zc = soc >= 11 ? 'Noble' : soc === 10 ? 'Intendant' : 'Prole';
            const zcColor = soc >= 11 ? 'var(--accent)' : soc === 10 ? 'var(--amber)' : 'var(--muted)';
            return `<span title="Zhodani social class" style="color:${zcColor}">CLASS<br><strong>${zc}</strong></span>`;
          })()}
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

      ${character.tas_member ? `
      <div class="sheet-section">
        <h3>TAS Membership</h3>
        <p class="empty" style="color:var(--accent)">✦ Travellers' Aid Society — Lifetime Member</p>
        <p class="empty">Access to Class A &amp; B starport lounges. 1 free High Passage every two months.</p>
      </div>` : ''}

      ${(character.clan_shares || 0) > 0 ? `
      <div class="sheet-section">
        <h3>Clan Shares</h3>
        <div class="credits-line">${character.clan_shares} Clan Share${character.clan_shares !== 1 ? 's' : ''}</div>
        <p class="empty">Can be traded for cash (Cr10,000 each), a corporation, political favours, or land (SOC 9+ male only). 3 Clan Shares = TER +1.</p>
      </div>` : ''}

      ${(character.reputation > 0) ? `
      <div class="sheet-section">
        <h3>Reputation (REP)</h3>
        <div class="credits-line">${character.reputation}</div>
        <p class="empty">Used for advancement in Bounty Hunter career.</p>
      </div>` : ''}

      ${(character.species_id === 'kkree') ? (() => {
        const degreeLabels = {
          servant_of_rankholder: 'Servant-of-Rankholder',
          kinsman_of_rankholder: 'Kinsman-of-Rankholder',
          rankholder: 'Rankholder',
        };
        const degree = degreeLabels[character.kkree_soc_rank_degree] || character.kkree_soc_rank_degree || '—';
        // Wives are now stored as Associate records with kind="wife"
        const wifeAssociates = (character.associates || []).filter(a => a.kind === 'wife');
        const wives = wifeAssociates.length;
        const members = (character.kkree_family_members || []);
        const roleCount = { warrior: 0, specialist: 0, servant: 0 };
        members.forEach(m => { if (roleCount[m.role] != null) roleCount[m.role]++; });
        const memberSummary = members.length
          ? `${roleCount.warrior} warrior${roleCount.warrior !== 1 ? 's' : ''}, ${roleCount.specialist} specialist${roleCount.specialist !== 1 ? 's' : ''}, ${roleCount.servant} servant${roleCount.servant !== 1 ? 's' : ''}`
          : 'No family members yet';
        return `
      <div class="sheet-section">
        <h3>K'kree Family</h3>
        <div class="stat-grid" style="grid-template-columns:repeat(3,1fr)">
          <div class="stat-cell"><span class="stat-label">SOC RANK</span><span class="stat-value" style="font-size:11px">${degree}</span></div>
          <div class="stat-cell"><span class="stat-label">WIVES</span><span class="stat-value">${wives}</span></div>
          <div class="stat-cell"><span class="stat-label">MEMBERS</span><span class="stat-value">${members.length}</span></div>
        </div>
        ${wives > 0 ? `<ul class="skill-list" style="margin-top:4px">${wifeAssociates.map(w => `<li>Wife — ${w.description || 'unnamed'}</li>`).join('')}</ul>` : `<p class="empty">No wives yet</p>`}
        ${members.length ? `<ul class="skill-list" style="margin-top:6px">${members.map(m => `<li>${m.role.charAt(0).toUpperCase() + m.role.slice(1)}${m.description ? ` — ${m.description}` : ''}</li>`).join('')}</ul>` : `<p class="empty">${memberSummary}</p>`}
        ${character.kkree_specialist_area ? `<p class="empty">Specialist area: ${character.kkree_specialist_area}</p>` : ''}
      </div>`;
      })() : ''}

      ${character.pension_per_year > 0 ? (() => {
        const _ex = new Set(['scout','rogue','prisoner','drifter']);
        const _qt = (character.term_history || []).filter(h => !_ex.has(h.career_id)).length;
        const _isSol = character.society_id === 'solomani_confederation';
        const _hasFullCareer = _isSol && (character.term_history || []).some(h => h.career_id === 'party' || h.career_id === 'solsec');
        const _pensionNote = _isSol
          ? (_hasFullCareer ? 'Full rate (Party/SolSec service). Collectible at Class A–B starports in the Confederation; SolSec also at Class C.'
                            : 'Solomani Confederation rate (½ Imperial). Collectible at Class A–B starports in the Confederation.')
          : `${_qt} qualifying term${_qt === 1 ? '' : 's'} (Scout/Rogue/Prisoner/Drifter excluded).`;
        return `
      <div class="sheet-section">
        <h3>Retirement Pension</h3>
        <div class="credits-line">Cr${character.pension_per_year.toLocaleString()}/year</div>
        <p class="empty">${_pensionNote}</p>
      </div>`;
      })() : ''}

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
        ${speciesNotesHTML}
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

      ${(character.knight_commander_by_deed || character.knight_commander_by_rank || character.knight_grand_cross) ? `
      <div class="sheet-section">
        <h3>Storm Knight Honours</h3>
        <ul class="skill-list">
          ${character.knight_grand_cross ? `<li><span>Knight Grand Cross Commander</span><span class="skill-level" style="color:var(--accent)">SOC≥12</span></li>` : ''}
          ${character.knight_commander_by_rank ? `<li><span>Knight Commander By Rank</span><span class="skill-level" style="color:var(--accent)">SOC≥10</span></li>` : ''}
          ${character.knight_commander_by_deed ? `<li><span>Knight Commander By Deed</span><span class="skill-level" style="color:var(--accent)">SOC≥10</span></li>` : ''}
          ${character.knight_commander_by_deed && character.knight_commander_by_rank ? `<li><span>Both Rank &amp; Deed</span><span class="skill-level" style="color:var(--accent)">SOC≥11</span></li>` : ''}
        </ul>
        <p class="empty">
          ${character.knight_grand_cross ? 'Grand Cross: SOC floor 12. ' : ''}
          ${character.knight_commander_by_deed && character.knight_commander_by_rank ? 'Both honours: SOC floor 11. ' :
            (character.knight_commander_by_deed || character.knight_commander_by_rank) ? 'Single honour: SOC floor 10. ' : ''}
        </p>
      </div>` : ''}

      ${character.solomani_passing ? `
      <div class="sheet-section">
        <h3>Solomani Passing Documents</h3>
        <p class="empty">Holding falsified genetic records — treated as Racial Solomani for career qualification (Party Patronage DM; Mixed Heritage penalty suppressed).</p>
        <p class="empty" style="color:var(--amber-dim)">Risk: natural 2 on survival in military/Party → SOC halved, documents revoked.</p>
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

/** Shorthand: safely escape any value for innerHTML interpolation. Handles null/undefined. */
const esc = s => escapeHTML(String(s ?? ''));

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
    case 'robot_build':
      stage.innerHTML = renderRobotBuildPhase();
      wireRobotBuildPhase();
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
    case 'aslan_setup':
      stage.innerHTML = renderAslanSetupPhase();
      wireAslanSetupPhase();
      break;
    case 'zhodani_training':
      stage.innerHTML = renderZhodaniTrainingPhase();
      wireZhodaniTrainingPhase();
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
      stage.innerHTML = `<div class="stage-content"><p>Unknown phase: ${esc(character.phase)}</p></div>`;
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

// ============================================================
// ROBOT BUILDER PHASE
// ============================================================

function getRobotConfig() {
  if (!character.robot_config) character.robot_config = structuredClone(ROBOT_DEFAULT_CONFIG);
  return robotNormalize(character.robot_config);
}

function saveRobotConfig(cfg) {
  character.robot_config = cfg;
  saveCharacter();
}

function renderRobotBuildPhase() {
  const cfg = getRobotConfig();
  const calc = calculateRobotConfig(cfg);
  const tab = uiState.robotTab || 'frame';
  const tl = rbN(cfg.techLevel, 12);

  const tabs = [
    { id:'frame',     label:'FRAME'       },
    { id:'brain',     label:'BRAIN'       },
    { id:'mobility',  label:'MOBILITY'    },
    { id:'equipment', label:'EQUIPMENT'   },
    { id:'skills',    label:'SKILLS'      },
    { id:'finalize',  label:'FINALIZE'    }
  ];

  // ── live totals bar (always shown) ──
  const slotsOver = calc.slots.used > calc.slots.total;
  const bwOver    = calc.bandwidth.used > calc.bandwidth.total;
  const totalsBar = `
    <div class="robot-totals">
      <div class="robot-total-cell ${slotsOver?'over':''}">
        <span class="robot-total-key">SLOTS</span>
        <span class="robot-total-val">${calc.slots.used}/${calc.slots.total}</span>
      </div>
      <div class="robot-total-cell ${bwOver?'over':''}">
        <span class="robot-total-key">BANDWIDTH</span>
        <span class="robot-total-val">${calc.bandwidth.used}/${calc.bandwidth.total}</span>
      </div>
      <div class="robot-total-cell">
        <span class="robot-total-key">HITS</span>
        <span class="robot-total-val">${calc.hits}</span>
      </div>
      <div class="robot-total-cell">
        <span class="robot-total-key">PROTECTION</span>
        <span class="robot-total-val">+${calc.armor.protection}</span>
      </div>
      <div class="robot-total-cell">
        <span class="robot-total-key">SPEED</span>
        <span class="robot-total-val">${calc.tacticalSpeed}m</span>
      </div>
      <div class="robot-total-cell">
        <span class="robot-total-key">COST</span>
        <span class="robot-total-val" style="font-size:14px">${rbFmtCr(calc.cost)}</span>
      </div>
    </div>`;

  // ── tab content ──
  let content = '';

  if (tab === 'frame') {
    const chassisCards = ROBOT_RULES.chassis.map(ch => `
      <div class="robot-option-card ${ch.id===cfg.chassisId?'selected':''}" data-rb-chassis="${ch.id}">
        <div class="robot-option-name">${ch.name}</div>
        <div class="robot-option-meta">
          <span class="robot-option-pill">${ch.slots} slots</span>
          <span class="robot-option-pill">${ch.hits} hits</span>
          <span class="robot-option-pill">${rbFmtCr(ch.basicCost)}</span>
        </div>
        <div class="robot-option-meta" style="margin-top:3px">${escapeHTML(ch.equivalent)}</div>
      </div>`).join('');
    content = `
      <div class="robot-section">
        <h3 class="robot-section-title">Chassis Size</h3>
        <div class="robot-option-grid">${chassisCards}</div>
      </div>
      <div class="robot-section">
        <h3 class="robot-section-title">Frame Modifications</h3>
        <div class="robot-fields">
          <div class="robot-field">
            <label>Added Armour (protection pts)</label>
            <input type="number" id="rb-armor-added" min="0" max="60" value="${cfg.frameMods.armorAdded}">
          </div>
          <div class="robot-field">
            <label>Power Packs (0–3)</label>
            <input type="number" id="rb-power-packs" min="0" max="3" value="${cfg.frameMods.powerPacks}">
          </div>
          <div class="robot-field">
            <label>Resilient Hits (added slots)</label>
            <input type="number" id="rb-resilient-hits" min="0" value="${cfg.frameMods.resilientHits}">
          </div>
          <div class="robot-field">
            <label>Light Hits (removed hits)</label>
            <input type="number" id="rb-light-hits" min="0" value="${cfg.frameMods.lightHits}">
          </div>
          <div class="robot-field">
            <label>Reduce Base Protection<br><small style="color:var(--muted)">-1 prot, saves 10% cost</small></label>
            <input type="checkbox" id="rb-reduce-prot" ${cfg.frameMods.reduceProtection?'checked':''}>
          </div>
          <div class="robot-field">
            <label>Efficiency Module<br><small style="color:var(--muted)">×2 endurance, +50% cost</small></label>
            <input type="checkbox" id="rb-efficiency" ${cfg.frameMods.efficiency?'checked':''}>
          </div>
        </div>
      </div>`;
  }

  if (tab === 'brain') {
    const brainCards = ROBOT_RULES.brains.map(br => `
      <div class="robot-option-card ${br.id===cfg.brainId?'selected':''}" data-rb-brain="${br.id}">
        <div class="robot-option-name">${br.name}</div>
        <div class="robot-option-meta">
          <span class="robot-option-pill">TL ${br.minTl}+</span>
          <span class="robot-option-pill">INT ${br.intelligence}</span>
          <span class="robot-option-pill">Computer/${br.computer}</span>
          <span class="robot-option-pill">${rbFmtCr(br.cost)}</span>
        </div>
        <div class="robot-option-meta" style="margin-top:3px">${escapeHTML((br.capabilities||[]).join(", "))}</div>
      </div>`).join('');
    const bwOptions = `<option value="">None</option>${ROBOT_RULES.bandwidthUpgrades.map(bw=>`<option value="${bw.id}" ${bw.id===cfg.bandwidthUpgradeId?'selected':''}>${bw.name} (${rbFmtCr(bw.cost)})</option>`).join('')}`;
    const brain = rbFindRule(ROBOT_RULES.brains, cfg.brainId);
    content = `
      <div class="robot-section">
        <h3 class="robot-section-title">Brain Type</h3>
        <div class="robot-option-grid">${brainCards}</div>
      </div>
      <div class="robot-section">
        <h3 class="robot-section-title">Brain Modifications</h3>
        <div class="robot-fields">
          <div class="robot-field">
            <label>Bandwidth Upgrade</label>
            <select id="rb-bw-upgrade">${bwOptions}</select>
          </div>
          <div class="robot-field">
            <label>INT Boost (0–3)<br><small style="color:var(--muted)">Uses bandwidth</small></label>
            <input type="number" id="rb-int-boost" min="0" max="3" value="${cfg.brainMods.intBoost}">
          </div>
          <div class="robot-field">
            <label>Hardened Brain<br><small style="color:var(--muted)">+50% brain cost</small></label>
            <input type="checkbox" id="rb-hardened" ${cfg.brainMods.hardened?'checked':''}>
          </div>
        </div>
        ${brain?`<p style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">
          Current INT: ${calc.intellect.finalInt} &nbsp;|&nbsp; Bandwidth: ${calc.bandwidth.used}/${calc.bandwidth.total}
        </p>`:''}
      </div>`;
  }

  if (tab === 'mobility') {
    const locoCards = ROBOT_RULES.locomotion.map(lo => `
      <div class="robot-option-card ${lo.id===cfg.locomotionId?'selected':''}" data-rb-loco="${lo.id}">
        <div class="robot-option-name">${lo.name}</div>
        <div class="robot-option-meta">
          <span class="robot-option-pill">TL ${lo.minTl}+</span>
          <span class="robot-option-pill">×${lo.multiplier} cost</span>
          ${lo.agility!=null?`<span class="robot-option-pill">Agility ${lo.agility>=0?'+':''}${lo.agility}</span>`:''}
          <span class="robot-option-pill">${lo.endurance}h</span>
        </div>
        <div class="robot-option-meta" style="margin-top:3px">${escapeHTML(lo.notes)}</div>
      </div>`).join('');
    const secLocoOptions = `<option value="">None</option>${ROBOT_RULES.locomotion.map(lo=>`<option value="${lo.id}" ${lo.id===cfg.mobilityMods.secondaryLocomotionId?'selected':''}>${lo.name}</option>`).join('')}`;
    content = `
      <div class="robot-section">
        <h3 class="robot-section-title">Primary Locomotion</h3>
        <div class="robot-option-grid">${locoCards}</div>
      </div>
      <div class="robot-section">
        <h3 class="robot-section-title">Enhancements</h3>
        <div class="robot-fields">
          <div class="robot-field">
            <label>Agility Boost (0–4)<br><small style="color:var(--muted)">×1/2/4/8 chassis cost</small></label>
            <input type="number" id="rb-agility-boost" min="0" max="4" value="${cfg.mobilityMods.agilityBoost}">
          </div>
          <div class="robot-field">
            <label>Speed Modifier (−12 to +12)<br><small style="color:var(--muted)">±10% cost per point</small></label>
            <input type="number" id="rb-speed-mod" min="-12" max="12" value="${cfg.mobilityMods.speedMod}">
          </div>
          <div class="robot-field">
            <label>Vehicle Speed Mode<br><small style="color:var(--muted)">Replaces tactical speed</small></label>
            <input type="checkbox" id="rb-vehicle-speed" ${cfg.mobilityMods.vehicleSpeed?'checked':''}>
          </div>
          <div class="robot-field">
            <label>Speed Band Boosts (0–3)</label>
            <input type="number" id="rb-vsb-boosts" min="0" max="3" value="${cfg.mobilityMods.vehicleSpeedBoosts}" ${cfg.mobilityMods.vehicleSpeed?'':'disabled'}>
          </div>
        </div>
        <p style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">
          Agility DM: ${calc.agility>=0?'+':''}${calc.agility} &nbsp;|&nbsp; Tactical speed: ${calc.tacticalSpeed}m &nbsp;|&nbsp; Endurance: ${calc.endurance}h
        </p>
      </div>
      <div class="robot-section">
        <h3 class="robot-section-title">Secondary Locomotion</h3>
        <div class="robot-fields">
          <div class="robot-field">
            <label>Secondary System</label>
            <select id="rb-sec-loco">${secLocoOptions}</select>
          </div>
        </div>
      </div>`;
  }

  if (tab === 'equipment') {
    // Manipulators
    const manipRows = cfg.manipulators.map((m,i) => {
      const stats = robotManipStats(tl, rbN(m.size,5), rbN(m.strBoost), rbN(m.dexBoost));
      return `
        <div class="robot-row-card">
          <label>Size<input type="number" data-rb-msize="${i}" min="1" max="10" value="${m.size}"></label>
          <label>Count<input type="number" data-rb-mcount="${i}" min="1" max="12" value="${m.count}"></label>
          <label>STR+<input type="number" data-rb-mstr="${i}" min="0" max="20" value="${m.strBoost}"></label>
          <label>DEX+<input type="number" data-rb-mdex="${i}" min="0" max="20" value="${m.dexBoost}"></label>
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">STR${stats.str}/DEX${stats.dex}</span>
          <button class="robot-remove-btn" data-rb-remove-manip="${i}">✕</button>
        </div>`;
    }).join('');
    // Systems checklist
    const sysChecks = ROBOT_RULES.systems.map(sys => {
      const checked = cfg.systems.includes(sys.id);
      const cost = robotSysCost(sys, calc.chassis);
      const slots = robotSysSlots(sys, calc.chassis);
      return `
        <div class="robot-check-row">
          <input type="checkbox" data-rb-sys="${sys.id}" ${checked?'checked':''}>
          <div class="robot-check-label">
            <div class="robot-check-name">${escapeHTML(sys.name)}</div>
            <div class="robot-check-desc">${escapeHTML(sys.notes||'')}${sys.minTl?` TL${sys.minTl}+.`:''} ${slots>0?`${slots} slots.`:''} ${cost>0?rbFmtCr(cost)+'.':''}</div>
          </div>
        </div>`;
    }).join('');
    // Custom options
    const customRows = cfg.customOptions.map((o,i) => `
      <div class="robot-row-card">
        <label>Name<input type="text" data-rb-cfield="name" data-rb-cidx="${i}" value="${escapeHTML(o.name)}"></label>
        <label>TL<input type="number" data-rb-cfield="minTl" data-rb-cidx="${i}" min="0" value="${o.minTl}"></label>
        <label>Slots<input type="number" data-rb-cfield="slots" data-rb-cidx="${i}" min="0" value="${o.slots}"></label>
        <label>Cost<input type="number" data-rb-cfield="cost" data-rb-cidx="${i}" step="100" value="${o.cost}"></label>
        <button class="robot-remove-btn" data-rb-remove-custom="${i}">✕</button>
      </div>`).join('');
    content = `
      <div class="robot-section">
        <h3 class="robot-section-title">Manipulators</h3>
        <p style="font-family:var(--font-mono);font-size:10px;color:var(--muted);margin-bottom:8px">Default: 2×Size ${calc.chassis?.size||5} manipulators included in chassis.</p>
        ${manipRows || '<p style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">No extra manipulators added.</p>'}
        <button class="btn ghost" id="rb-add-manip" style="margin-top:4px">+ ADD MANIPULATOR</button>
      </div>
      <div class="robot-section">
        <h3 class="robot-section-title">Installed Systems</h3>
        <div class="robot-check-grid">${sysChecks}</div>
      </div>
      <div class="robot-section">
        <h3 class="robot-section-title">Custom Options / Weapons</h3>
        ${customRows || '<p style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">No custom options added.</p>'}
        <button class="btn ghost" id="rb-add-custom" style="margin-top:4px">+ ADD CUSTOM OPTION</button>
      </div>`;
  }

  if (tab === 'skills') {
    const skillRows = cfg.skills.map((sk,i) => {
      const skillOpts = ROBOT_RULES.skills.map(s=>`<option value="${escapeHTML(s.name)}" ${s.name===sk.name?'selected':''}>${escapeHTML(s.name)}</option>`).join('');
      const levelOpts = [0,1,2,3,4].map(l=>`<option value="${l}" ${l===rbN(sk.level)?'selected':''}>${l}</option>`).join('');
      const pkg = ROBOT_RULES.skills.find(s=>s.name===sk.name)||ROBOT_RULES.skills[0];
      const lv=rbN(sk.level);
      const bw=pkg.bandwidth+lv;
      const cost=pkg.baseCost*(10**lv);
      // Specialty dropdown for cascade skills (reuses the main CASCADE_SKILLS map)
      const specialties = CASCADE_SKILLS[sk.name] || null;
      const specHtml = specialties ? `
        <label>Specialty<select data-rb-skspec="${i}">
          <option value="">— any —</option>
          ${specialties.map(sp=>`<option value="${escapeHTML(sp)}" ${sp===(sk.specialty||'')?'selected':''}>${escapeHTML(sp)}</option>`).join('')}
        </select></label>` : '';
      return `
        <div class="robot-row-card">
          <label>Skill<select data-rb-skname="${i}">${skillOpts}</select></label>
          <label>Level<select data-rb-sklevel="${i}">${levelOpts}</select></label>
          ${specHtml}
          <span style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">${bw>0?`BW ${bw}`:''} ${rbFmtCr(cost)}</span>
          <button class="robot-remove-btn" data-rb-remove-skill="${i}">✕</button>
        </div>`;
    }).join('');
    content = `
      <div class="robot-section">
        <h3 class="robot-section-title">Skill Software Packages</h3>
        <p style="font-family:var(--font-mono);font-size:10px;color:var(--muted);margin-bottom:8px">
          Each skill costs bandwidth equal to skill level. Max level 3 per package (Level 4 requires Referee approval).
        </p>
        ${skillRows || '<p style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">No skill packages installed.</p>'}
        <button class="btn ghost" id="rb-add-skill" style="margin-top:4px">+ ADD SKILL PACKAGE</button>
      </div>`;
  }

  if (tab === 'finalize') {
    const chars = robotFoundryChars(cfg, calc);
    const validation = validateRobotConfig(cfg, calc);
    const hasErrors = validation.some(m=>m.type==='error');
    const charCells = ['STR','DEX','END','INT','EDU','SOC'].map(k=>`
      <div class="robot-char-cell">
        <span class="robot-char-key">${k}</span>
        <span class="robot-char-val">${chars[k]||0}</span>
      </div>`).join('');
    content = `
      <div class="robot-section">
        <h3 class="robot-section-title">Robot Identity</h3>
        <div class="robot-fields">
          <div class="robot-field" style="flex:1">
            <label>Designation (Name)</label>
            <input type="text" id="rb-name" value="${escapeHTML(cfg.name||'')}" placeholder="New Robot" style="min-width:200px">
          </div>
          <div class="robot-field" style="flex:2">
            <label>Purpose / Role</label>
            <input type="text" id="rb-purpose" value="${escapeHTML(cfg.purpose||'')}" placeholder="Combat/Labour/Medical..." style="min-width:200px">
          </div>
          <div class="robot-field">
            <label>Tech Level</label>
            <input type="number" id="rb-tl" min="5" max="20" value="${tl}">
          </div>
        </div>
        <div class="robot-field" style="width:100%">
          <label>Notes</label>
          <input type="text" id="rb-notes" value="${escapeHTML(cfg.notes||'')}" placeholder="Additional notes..." style="width:100%;min-width:200px">
        </div>
      </div>
      <div class="robot-section">
        <h3 class="robot-section-title">Derived Characteristics (for Foundry / Sheet)</h3>
        <div class="robot-char-grid">${charCells}</div>
        <p style="font-family:var(--font-mono);font-size:10px;color:var(--muted)">
          STR = manipulator STR &nbsp;|&nbsp; DEX = manipulator DEX + agility &nbsp;|&nbsp; END = hits &nbsp;|&nbsp; INT = brain INT &nbsp;|&nbsp; EDU = total bandwidth
        </p>
      </div>
      <div class="robot-section">
        <h3 class="robot-section-title">Build Validation</h3>
        <div class="robot-validation">
          ${validation.map(m=>`<div class="robot-val-item ${m.type}">${escapeHTML(m.text)}</div>`).join('')}
        </div>
      </div>
      <div class="robot-summary-block">
        <h4>Frame</h4>
        <p>${calc.chassis?.name||'None'} / ${calc.locomotion?.name||'None'} · Hits ${calc.hits} · Protection +${calc.armor.protection} · Speed ${calc.tacticalSpeed}m · Endurance ${calc.endurance}h</p>
      </div>
      <div class="robot-summary-block">
        <h4>Brain</h4>
        <p>${calc.brain?.name||'None'} · INT ${calc.intellect.finalInt} · Computer/${calc.brain?.computer??0} · BW ${calc.bandwidth.used}/${calc.bandwidth.total}</p>
      </div>
      <div class="robot-summary-block">
        <h4>Skills</h4>
        <p>${calc.skills.map(sk=>`${sk.name}${sk.specialty?` (${sk.specialty})`:''} ${sk.level}`).join(', ')||'None'}</p>
      </div>
      <div class="robot-summary-block">
        <h4>Traits</h4>
        <p>${calc.traits.join(', ')||'None'}</p>
      </div>
      <div class="phase-actions" style="margin-top:14px">
        <button class="btn primary" id="rb-finalize-btn" ${hasErrors?'disabled':''}>FINALIZE ROBOT →</button>
        <button class="btn ghost" id="rb-back-btn">← BACK TO DICE</button>
      </div>
      ${hasErrors?'<p style="font-family:var(--font-mono);font-size:10px;color:var(--danger);margin-top:6px">Fix errors above before finalizing.</p>':''}`;
  }

  return `
    <div class="panel-header"><span class="led"></span><span>ROBOT CONSTRUCTION — ${escapeHTML(cfg.name||'New Robot')} · TL${tl}</span></div>
    <div class="stage-content">
      <div class="phase-label">Robot Build Phase</div>
      <h2 class="phase-title">Build Your Robot</h2>

      ${totalsBar}

      <div class="robot-tabs">
        ${tabs.map(t=>`<button class="robot-tab-btn ${t.id===tab?'active':''}" data-robot-tab="${t.id}">${t.label}</button>`).join('')}
      </div>

      ${content}
    </div>`;
}

function wireRobotBuildPhase() {
  // Tab switching
  document.querySelectorAll('[data-robot-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      uiState.robotTab = btn.dataset.robotTab;
      renderAll();
    });
  });

  const cfg = getRobotConfig();

  // ── FRAME tab ──
  document.querySelectorAll('[data-rb-chassis]').forEach(el => {
    el.addEventListener('click', () => {
      cfg.chassisId = el.dataset.rbChassis;
      saveRobotConfig(cfg); renderAll();
    });
  });
  document.querySelectorAll('[data-rb-loco]').forEach(el => {
    el.addEventListener('click', () => {
      cfg.locomotionId = el.dataset.rbLoco;
      saveRobotConfig(cfg); renderAll();
    });
  });
  const wireNumericField = (id, obj, key) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('change', () => { obj[key] = rbN(el.value); saveRobotConfig(cfg); renderAll(); });
  };
  const wireCheckField = (id, obj, key) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('change', () => { obj[key] = el.checked; saveRobotConfig(cfg); renderAll(); });
  };
  wireNumericField('rb-armor-added',   cfg.frameMods, 'armorAdded');
  wireNumericField('rb-power-packs',   cfg.frameMods, 'powerPacks');
  wireNumericField('rb-resilient-hits',cfg.frameMods, 'resilientHits');
  wireNumericField('rb-light-hits',    cfg.frameMods, 'lightHits');
  wireCheckField('rb-reduce-prot',     cfg.frameMods, 'reduceProtection');
  wireCheckField('rb-efficiency',      cfg.frameMods, 'efficiency');

  // ── BRAIN tab ──
  document.querySelectorAll('[data-rb-brain]').forEach(el => {
    el.addEventListener('click', () => {
      cfg.brainId = el.dataset.rbBrain;
      saveRobotConfig(cfg); renderAll();
    });
  });
  const bwEl = document.getElementById('rb-bw-upgrade');
  if (bwEl) bwEl.addEventListener('change', () => { cfg.bandwidthUpgradeId = bwEl.value; saveRobotConfig(cfg); renderAll(); });
  wireNumericField('rb-int-boost', cfg.brainMods, 'intBoost');
  wireCheckField('rb-hardened',    cfg.brainMods, 'hardened');

  // ── MOBILITY tab ──
  wireNumericField('rb-agility-boost', cfg.mobilityMods, 'agilityBoost');
  wireNumericField('rb-speed-mod',     cfg.mobilityMods, 'speedMod');
  wireCheckField('rb-vehicle-speed',   cfg.mobilityMods, 'vehicleSpeed');
  wireNumericField('rb-vsb-boosts',    cfg.mobilityMods, 'vehicleSpeedBoosts');
  const secLoEl = document.getElementById('rb-sec-loco');
  if (secLoEl) secLoEl.addEventListener('change', () => { cfg.mobilityMods.secondaryLocomotionId = secLoEl.value; saveRobotConfig(cfg); renderAll(); });

  // ── EQUIPMENT tab — manipulators ──
  document.querySelectorAll('[data-rb-msize],[data-rb-mcount],[data-rb-mstr],[data-rb-mdex]').forEach(inp => {
    inp.addEventListener('change', () => {
      const i = rbN(inp.dataset.rbMsize ?? inp.dataset.rbMcount ?? inp.dataset.rbMstr ?? inp.dataset.rbMdex);
      if (inp.dataset.rbMsize  !== undefined) cfg.manipulators[i].size     = Math.max(1, rbN(inp.value));
      if (inp.dataset.rbMcount !== undefined) cfg.manipulators[i].count    = Math.max(1, rbN(inp.value));
      if (inp.dataset.rbMstr   !== undefined) cfg.manipulators[i].strBoost = Math.max(0, rbN(inp.value));
      if (inp.dataset.rbMdex   !== undefined) cfg.manipulators[i].dexBoost = Math.max(0, rbN(inp.value));
      saveRobotConfig(cfg); renderAll();
    });
  });
  document.querySelectorAll('[data-rb-remove-manip]').forEach(btn => {
    btn.addEventListener('click', () => { cfg.manipulators.splice(rbN(btn.dataset.rbRemoveManip),1); saveRobotConfig(cfg); renderAll(); });
  });
  document.getElementById('rb-add-manip')?.addEventListener('click', () => {
    const chassis = rbFindRule(ROBOT_RULES.chassis, cfg.chassisId);
    cfg.manipulators.push({ size: chassis?.size||5, count:1, strBoost:0, dexBoost:0 });
    saveRobotConfig(cfg); renderAll();
  });
  // systems checkboxes
  document.querySelectorAll('[data-rb-sys]').forEach(cb => {
    cb.addEventListener('change', () => {
      const id = cb.dataset.rbSys;
      cfg.systems = cb.checked ? [...new Set([...cfg.systems,id])] : cfg.systems.filter(x=>x!==id);
      saveRobotConfig(cfg); renderAll();
    });
  });
  // custom options
  document.querySelectorAll('[data-rb-cfield]').forEach(inp => {
    inp.addEventListener('change', () => {
      const i = rbN(inp.dataset.rbCidx), field = inp.dataset.rbCfield;
      if (!cfg.customOptions[i]) return;
      cfg.customOptions[i][field] = ['minTl','slots','cost'].includes(field) ? rbN(inp.value) : inp.value;
      saveRobotConfig(cfg); renderAll();
    });
  });
  document.querySelectorAll('[data-rb-remove-custom]').forEach(btn => {
    btn.addEventListener('click', () => { cfg.customOptions.splice(rbN(btn.dataset.rbRemoveCustom),1); saveRobotConfig(cfg); renderAll(); });
  });
  document.getElementById('rb-add-custom')?.addEventListener('click', () => {
    cfg.customOptions.push({ name:'Custom Option', minTl:rbN(cfg.techLevel,12), slots:0, cost:0, traits:'', notes:'' });
    saveRobotConfig(cfg); renderAll();
  });

  // ── SKILLS tab ──
  document.querySelectorAll('[data-rb-skname],[data-rb-sklevel],[data-rb-skspec]').forEach(inp => {
    inp.addEventListener('change', () => {
      const i = rbN(inp.dataset.rbSkname ?? inp.dataset.rbSklevel ?? inp.dataset.rbSkspec);
      if (inp.dataset.rbSkname  !== undefined) {
        cfg.skills[i].name = inp.value;
        cfg.skills[i].specialty = ''; // reset specialty when skill changes
      }
      if (inp.dataset.rbSklevel !== undefined) cfg.skills[i].level = rbN(inp.value);
      if (inp.dataset.rbSkspec  !== undefined) cfg.skills[i].specialty = inp.value;
      saveRobotConfig(cfg); renderAll();
    });
  });
  document.querySelectorAll('[data-rb-remove-skill]').forEach(btn => {
    btn.addEventListener('click', () => { cfg.skills.splice(rbN(btn.dataset.rbRemoveSkill),1); saveRobotConfig(cfg); renderAll(); });
  });
  document.getElementById('rb-add-skill')?.addEventListener('click', () => {
    cfg.skills.push({ name: ROBOT_RULES.skills[0].name, level:0 });
    saveRobotConfig(cfg); renderAll();
  });

  // ── FINALIZE tab ──
  const nameEl = document.getElementById('rb-name');
  if (nameEl) nameEl.addEventListener('change', () => { cfg.name = nameEl.value; saveRobotConfig(cfg); renderAll(); });
  const purposeEl = document.getElementById('rb-purpose');
  if (purposeEl) purposeEl.addEventListener('change', () => { cfg.purpose = purposeEl.value; saveRobotConfig(cfg); renderAll(); });
  const tlEl = document.getElementById('rb-tl');
  if (tlEl) tlEl.addEventListener('change', () => { cfg.techLevel = rbN(tlEl.value, 12); saveRobotConfig(cfg); renderAll(); });
  const notesEl = document.getElementById('rb-notes');
  if (notesEl) notesEl.addEventListener('change', () => { cfg.notes = notesEl.value; saveRobotConfig(cfg); renderAll(); });

  document.getElementById('rb-back-btn')?.addEventListener('click', () => {
    // Return to new biological character (fresh start)
    if (!confirm('Go back to dice rolling? Your robot build will be saved but you will start a new character.')) return;
    character.phase = 'characteristics';
    character.character_type = 'biological';
    saveCharacter();
    renderAll();
  });

  document.getElementById('rb-finalize-btn')?.addEventListener('click', async () => {
    const finalCfg = robotNormalize(character.robot_config);
    const calc = calculateRobotConfig(finalCfg);
    const chars = robotFoundryChars(finalCfg, calc);
    // Set characteristics on the character before sending
    character.characteristics = { STR:chars.STR, DEX:chars.DEX, END:chars.END, INT:chars.INT, EDU:chars.EDU, SOC:chars.SOC };
    try {
      const resp = await fetch('/api/robot/finalize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ character, robot_config: finalCfg })
      });
      if (!resp.ok) { const err = await resp.json(); throw new Error(err.detail || 'Finalize failed'); }
      const data = await resp.json();
      character = data.character;
      saveCharacter();
      renderAll();
    } catch(e) { alert('Failed to finalize robot: ' + e.message); }
  });
}

// ── end robot builder phase ──────────────────────────────────

function renderCharacteristicsPhase() {
  const hasRolled = Object.values(character.characteristics).some(v => v > 0);
  const _socLbl = socLabelForChar(character);
  const STATS = ['STR', 'DEX', 'END', 'INT', 'EDU', ...(_socLbl ? ['SOC'] : [])];
  const STAT_LABELS = { STR:'STR', DEX:'DEX', END:'END', INT:'INT', EDU:'EDU', SOC: _socLbl || 'SOC' };

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
            <span class="stat-label">${STAT_LABELS[stat]}</span>
            <span class="stat-value">${val}</span>
            <span class="stat-dm">DM ${formatDM(dm)}</span>
            ${(uiState.gmMode || character.boon_rolls_remaining > 0) ? `
              <button class="boon-btn" data-boon-stat="${stat}" title="Re-roll ${STAT_LABELS[stat]}, keep the higher value">BOON</button>
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
        <span class="rq-stat"><span class="rq-k">BEST</span><span class="rq-v">${STAT_LABELS[bestStat]} ${character.characteristics[bestStat]}</span></span>
        <span class="rq-stat"><span class="rq-k">WORST</span><span class="rq-v">${STAT_LABELS[worstStat]} ${character.characteristics[worstStat]}</span></span>
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
        ${STATS.map(s => `<option value="${s}" ${s === (uiState.swapA || 'EDU') ? 'selected' : ''}>${STAT_LABELS[s]} (${character.characteristics[s]})</option>`).join('')}
      </select>
      <span class="swap-arrow">↔</span>
      <select id="swap-b" class="swap-select">
        ${STATS.map(s => `<option value="${s}" ${s === (uiState.swapB || 'STR') ? 'selected' : ''}>${STAT_LABELS[s]} (${character.characteristics[s]})</option>`).join('')}
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
        <div class="robot-divider">— or —</div>
        <button class="btn" id="btn-build-robot">I WANT TO PLAY A ROBOT</button>
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
  document.getElementById('btn-build-robot').addEventListener('click', async () => {
    try {
      const response = await fetch('/api/robot/new', { method: 'POST' });
      const data = await response.json();
      character = data.character;
      character.robot_config = structuredClone(ROBOT_DEFAULT_CONFIG);
      uiState.robotTab = 'frame';
      saveCharacter();
      renderAll();
    } catch(e) { alert('Failed to start robot build: ' + e.message); }
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

function renderSpeciesSkillGrantChoice() {
  const pc = uiState.speciesSkillGrantPending;
  const opts = pc.options || [];
  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02b — SPECIES SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Species Ability</div>
      <h2 class="phase-title">Choose Your Combat Skill</h2>
      <p class="phase-subtitle">${esc(pc.prompt || 'Choose one skill granted by your species:')}</p>
      <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:16px">
        ${opts.map(o => `
          <button class="card species-skill-grant-opt" data-skill-choice="${escapeAttr(o.id)}"
                  style="flex:1;min-width:200px;text-align:left;cursor:pointer">
            <div class="card-title">${esc(o.label)}</div>
            <div class="card-desc">${esc(o.description)}</div>
          </button>
        `).join('')}
      </div>
    </div>
  `;
}

function renderSpeciesCasteChoice() {
  const pc = uiState.speciesCasteChoicePending;
  const opts = pc.options || [];
  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02b — SPECIES SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">${esc(pc.species_name)} — Caste</div>
      <h2 class="phase-title">Choose Your Caste</h2>
      <p class="phase-subtitle">${esc(pc.species_name)} society is organised around four castes, each with different characteristic modifiers. Your caste is determined at birth and shapes your place in society for life.</p>
      <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:16px">
        ${opts.map(o => {
          const sp = SPECIES.find(s => s.id === o.id);
          const modsText = sp ? Object.entries(sp.characteristic_modifiers || {})
            .filter(([, v]) => v !== 0)
            .map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`)
            .join(' · ') : '';
          return `
            <button class="card species-caste-opt" data-caste-id="${escapeAttr(o.id)}"
                    style="flex:1;min-width:200px;text-align:left;cursor:pointer">
              <div class="card-title">${esc(o.label)}</div>
              ${modsText ? `<div class="card-meta">${esc(modsText)}</div>` : ''}
              <div class="card-desc">${esc(o.description)}</div>
            </button>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

function renderZhodaniPsiChoice() {
  const pc = uiState.zhodaniPsiPending;
  const opts = pc.options || [];
  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02b — SPECIES SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Zhodani Consulate</div>
      <h2 class="phase-title">Zhodani — PSI Ruleset</h2>
      <p class="phase-subtitle">Choose which rulebook's PSI mechanic to use for this character.</p>
      <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:16px">
        ${opts.map(o => `
          <button class="card zhodani-psi-opt" data-ruleset="${escapeAttr(o.id)}"
                  style="flex:1;min-width:220px;text-align:left;cursor:pointer">
            <div class="card-title">${esc(o.label)}</div>
            <div class="card-desc" style="white-space:pre-line">${esc(o.description)}</div>
          </button>
        `).join('')}
      </div>
    </div>
  `;
}

// Normalise a species' freeform `source` string into a clean sourcebook label
// so the "other alien races" list can be grouped by book. Order is controlled
// by SPECIES_BOOK_ORDER below.
function speciesBookLabel(source) {
  const s = (source || '').toLowerCase();
  if (s.includes('spinward extents')) return 'The Spinward Extents';
  if (s.includes('pirates of drinax')) return 'Pirates of Drinax';
  if (s.includes('glorious empire')) return 'The Glorious Empire';
  if (s.includes('vol. 2') || s.includes('volume 2')) return 'Aliens of Charted Space, Vol. 2';
  if (s.includes('vol. 5') || s.includes('volume 5')) return 'Aliens of Charted Space, Vol. 5';
  if (s.includes('vol. 1') || s.includes('volume 1')) return 'Aliens of Charted Space, Vol. 1';
  if (s.includes('aliens of charted space')) return 'Aliens of Charted Space';
  if (s.includes('solomani')) return 'Solomani Confederation';
  if (s.includes('hiver')) return 'Hiver Federation';
  if (s.includes("k'kree") || s.includes('kkree')) return "K'kree";
  if (s.includes('core rulebook') || s.includes('frontier human') || s.includes('spinward marches')) {
    return 'Core Rulebook & Setting';
  }
  return 'Other Supplements';
}
const SPECIES_BOOK_ORDER = {
  'Core Rulebook & Setting': 0,
  'Aliens of Charted Space': 1,
  'Aliens of Charted Space, Vol. 1': 2,
  'Aliens of Charted Space, Vol. 2': 3,
  'Aliens of Charted Space, Vol. 5': 4,
  'The Spinward Extents': 5,
  'Pirates of Drinax': 6,
  'The Glorious Empire': 7,
  'Solomani Confederation': 8,
  'Hiver Federation': 9,
  "K'kree": 10,
  'Other Supplements': 99,
};

function renderSpeciesPhase() {
  // If a Heritage Roll result is pending, show the result panel instead
  if (uiState.racialBackgroundResult) {
    return renderRacialBackgroundResult();
  }
  // If a species skill grant choice is pending (e.g. Dynchia Warrior People)
  if (uiState.speciesSkillGrantPending) {
    return renderSpeciesSkillGrantChoice();
  }
  // If a Zhodani PSI ruleset choice is pending, show that panel
  if (uiState.zhodaniPsiPending) {
    return renderZhodaniPsiChoice();
  }
  // If a species caste choice is pending (e.g. Souggvuez)
  if (uiState.speciesCasteChoicePending) {
    return renderSpeciesCasteChoice();
  }

  const selected = uiState.selectedSpecies || character.species_id;
  const speciesApplied = character.species_id && character.traits && character.traits.length >= 0 && character.phase !== 'species';

  // Filter species list by the selected society
  const activeSociety = SOCIETIES.find(s => s.id === (character.society_id || 'third_imperium'));
  const allowedIds = activeSociety ? new Set(activeSociety.species_ids) : null;
  const filteredSpecies = allowedIds ? SPECIES.filter(sp => allowedIds.has(sp.id)) : SPECIES;

  const renderSpeciesCard = (sp) => {
    const isRollTrigger = !!sp.racial_background_roll;
    const _fmtCustomRoll = v => v.replace('fixed:', 'always ').replace('_min', ' min ');
    const modsText = isRollTrigger
      ? '2D Heritage Roll'
      : (() => {
          const stdMods = Object.entries(sp.characteristic_modifiers || {})
            .filter(([, v]) => v !== 0)
            .map(([k, v]) => `${k} ${v > 0 ? '+' : ''}${v}`);
          const customRolls = Object.entries(sp.custom_characteristic_rolls || {})
            .filter(([, v]) => v !== '2D')
            .map(([k, v]) => `${k}: ${_fmtCustomRoll(v)}`);
          const all = [...stdMods, ...customRolls];
          if (all.length > 0) return all.join(' · ');
          if (sp.eslyat_subraces) return 'STR +1 (male) · SOC varies by caste';
          if (sp.gender_modifiers) return 'Varies by gender';
          if (sp.droyne_caste_system) return 'Varies by caste';
          if (sp.caste_choice) return 'Varies by caste — pick at selection';
          return 'No modifiers';
        })();
    return `
      <button class="card ${selected === sp.id ? 'selected' : ''}" data-species="${sp.id}">
        <div class="card-title">${sp.name}</div>
        <div class="card-meta">${modsText}</div>
        <div class="card-desc">${sp.description}</div>
        ${isRollTrigger ? '<div class="card-meta" style="color:var(--amber)">🎲 Roll determines your exact heritage</div>' : ''}
      </button>
    `;
  };

  // Split the filtered list into a "common" set (shown by default) and the rest
  // ("other alien races"), which are grouped by sourcebook and collapsed so the
  // picker isn't overwhelming. Small societies (no common set, short list) keep
  // the original flat grid.
  const commonIds = (activeSociety && activeSociety.common_species_ids) || [];
  const commonIdSet = new Set(commonIds);
  const hasCommon = filteredSpecies.some(sp => commonIdSet.has(sp.id));
  const groupOther = hasCommon || filteredSpecies.length > 12;

  let speciesPickerHTML;
  if (!groupOther) {
    speciesPickerHTML = `<div class="card-grid">${filteredSpecies.map(renderSpeciesCard).join('')}</div>`;
  } else {
    const commonSpecies = hasCommon ? filteredSpecies.filter(sp => commonIdSet.has(sp.id)) : [];
    const otherSpecies = filteredSpecies.filter(sp => !commonIdSet.has(sp.id));

    // Bucket the "other" species by normalised book label.
    const books = {};
    otherSpecies.forEach(sp => {
      const label = speciesBookLabel(sp.source);
      (books[label] = books[label] || []).push(sp);
    });
    const bookOrder = Object.keys(books).sort((a, b) =>
      (SPECIES_BOOK_ORDER[a] ?? 50) - (SPECIES_BOOK_ORDER[b] ?? 50) || a.localeCompare(b));

    // Before any interaction speciesOpenBooks is undefined → default the first
    // book open so there's always visible content; once the user toggles
    // anything, their explicit open/closed state takes over.
    const openMap = uiState.speciesOpenBooks;
    const bookSectionsHTML = bookOrder.map((book, idx) => {
      const open = openMap ? !!openMap[book] : idx === 0;
      return `
        <div class="species-book${open ? ' open' : ''}">
          <button type="button" class="species-book-toggle" data-book="${escapeAttr(book)}">
            <span class="species-book-caret">${open ? '▾' : '▸'}</span>
            <span class="species-book-name">${esc(book)}</span>
            <span class="species-book-count">${books[book].length}</span>
          </button>
          ${open ? `<div class="card-grid">${books[book].map(renderSpeciesCard).join('')}</div>` : ''}
        </div>`;
    }).join('');

    if (hasCommon) {
      const expanded = !!uiState.speciesExpandOther;
      speciesPickerHTML = `
        <div class="card-grid">${commonSpecies.map(renderSpeciesCard).join('')}</div>
        <div class="species-other-wrap">
          <button type="button" class="species-other-toggle${expanded ? ' open' : ''}" id="btn-species-other">
            <span class="species-book-caret">${expanded ? '▾' : '▸'}</span>
            <span class="species-book-name">Other alien races</span>
            <span class="species-book-count">${otherSpecies.length}</span>
          </button>
          ${expanded ? `<div class="species-book-list">${bookSectionsHTML}</div>` : ''}
        </div>`;
    } else {
      speciesPickerHTML = `<div class="species-book-list">${bookSectionsHTML}</div>`;
    }
  }

  const selectedSp = SPECIES.find(s => s.id === selected);
  const _spNotes = selectedSp && selectedSp.species_notes && selectedSp.species_notes.length
    ? `<div class="species-notes-panel"><h5>Mechanical Notes</h5><ul class="species-notes-list">${selectedSp.species_notes.map(n => `<li>${esc(n)}</li>`).join('')}</ul></div>`
    : '';
  const traitsPanel = selectedSp && selectedSp.traits.length ? `
    <div class="species-traits-panel">
      <h4>Species Traits — ${esc(selectedSp.name)}</h4>
      ${selectedSp.traits.map(t => `
        <div class="trait">
          <span class="trait-name">${esc(t.name)}</span>
          <span class="trait-desc">${esc(t.description)}</span>
        </div>
      `).join('')}
      ${_spNotes}
    </div>
  ` : (selectedSp ? `<p class="empty" style="margin-top:14px">No special traits. The baseline Traveller experience.</p>${_spNotes}` : '');

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 02b — SPECIES SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Genetic Profile</div>
      <h2 class="phase-title">Choose Your Species</h2>
      <p class="phase-subtitle">Species modifiers apply immediately to your rolled characteristics.</p>

      <div class="species-intro">
        <p>
          ${activeSociety
            ? `Showing species available to characters raised in the <strong>${esc(activeSociety.name)}</strong>.`
            : 'Showing all available species.'
          }
          Species modifiers apply once, now, to the characteristics you just rolled.
        </p>
        <p class="species-intro-hint">
          <em>Single-click to preview traits · Double-click to apply immediately.</em>
        </p>
      </div>

      ${speciesPickerHTML}

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
        <div style="font-size:20px;font-weight:700">${esc(result.result_name)}</div>
        ${mods ? `<div style="font-size:12px;color:var(--text-dim);margin-top:4px">Characteristic modifiers: ${mods}</div>` : ''}
        ${resolvedSp?.description ? `<p style="font-size:13px;margin-top:10px">${esc(resolvedSp.description)}</p>` : ''}
      </div>

      ${resolvedSp?.traits?.length ? `
        <div class="species-traits-panel">
          <h4>Heritage Traits — ${esc(resolvedSp.name)}</h4>
          ${resolvedSp.traits.map(t => `
            <div class="trait">
              <span class="trait-name">${esc(t.name)}</span>
              <span class="trait-desc">${esc(t.description)}</span>
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

  // Caste choice (e.g. Souggvuez) — clicking a caste card applies the variant
  if (uiState.speciesCasteChoicePending) {
    document.querySelectorAll('.species-caste-opt').forEach(btn => {
      btn.addEventListener('click', async () => {
        const casteId = btn.getAttribute('data-caste-id');
        try {
          const response = await apiCall('/api/character/apply-species', { species_id: casteId });
          await applyResponse(response);
          uiState.speciesCasteChoicePending = null;
          // Handle any further pending choices the caste variant might trigger
          if (response && response.pending_choice?.kind === 'species_skill_grant') {
            uiState.speciesSkillGrantPending = response.pending_choice;
            renderStage();
            return;
          }
          character.phase = 'background';
          saveCharacter();
          renderAll();
        } catch (e) { alert(e.message); }
      });
    });
    return;
  }

  // Species skill grant choice — wire the option cards (e.g. Dynchia)
  if (uiState.speciesSkillGrantPending) {
    document.querySelectorAll('.species-skill-grant-opt').forEach(btn => {
      btn.addEventListener('click', async () => {
        const skillChoice = btn.getAttribute('data-skill-choice');
        try {
          const response = await apiCall('/api/character/life-event-choice', { choice: skillChoice });
          await applyResponse(response);
          uiState.speciesSkillGrantPending = null;
          character.phase = 'background';
          saveCharacter();
          renderAll();
        } catch (e) { alert(e.message); }
      });
    });
    return;
  }

  // Zhodani PSI ruleset choice — wire the two option cards
  if (uiState.zhodaniPsiPending) {
    document.querySelectorAll('.zhodani-psi-opt').forEach(btn => {
      btn.addEventListener('click', async () => {
        const ruleset = btn.getAttribute('data-ruleset');
        try {
          const response = await apiCall('/api/character/resolve-zhodani-psi-choice', { ruleset });
          await applyResponse(response);
          uiState.zhodaniPsiPending = null;
          if (response && response.needs_zhodani_training) {
            // phase already set to 'zhodani_training' by engine
          } else {
            character.phase = 'background';
          }
          saveCharacter();
          renderAll();
        } catch (e) { alert(e.message); }
      });
    });
    return;
  }

  // Shared apply logic — used by both double-click on card and the confirm button.
  async function applySelectedSpecies() {
    if (!uiState.selectedSpecies) return;
    try {
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
      // Species skill grant choice (e.g. Dynchia Warrior People)
      if (response && response.pending_choice?.kind === 'species_skill_grant') {
        uiState.speciesSkillGrantPending = response.pending_choice;
        renderStage();
        return;
      }
      // Zhodani PSI ruleset choice: show the two-option panel before progressing
      if (response && response.pending_choice?.kind === 'zhodani_psi_ruleset') {
        uiState.zhodaniPsiPending = response.pending_choice;
        renderStage();
        return;
      }
      // Caste-choice species (e.g. Souggvuez): show caste picker before applying
      if (response && response.pending_choice?.kind === 'species_caste_choice') {
        uiState.speciesCasteChoicePending = response.pending_choice;
        renderStage();
        return;
      }
      // Aslan Hierate: skip background/pre_career, go directly to aslan_setup
      if (response && response.needs_aslan_setup) {
        // phase is already set to 'aslan_setup' by the engine
      } else if (response && response.needs_zhodani_training) {
        // Zhodani Noble/Intendant: psionic training before background
        // phase is already set to 'zhodani_training' by the engine
      } else {
        character.phase = 'background';
      }
      saveCharacter();
      renderAll();
    } catch (e) { alert(e.message); }
  }

  // "Other alien races" master expander (societies with a common set)
  const otherToggle = document.getElementById('btn-species-other');
  if (otherToggle) {
    otherToggle.addEventListener('click', () => {
      uiState.speciesExpandOther = !uiState.speciesExpandOther;
      renderStage();
    });
  }
  // Per-sourcebook collapse toggles. Lazily materialise speciesOpenBooks on the
  // first interaction (until then the renderer defaults the first book open).
  document.querySelectorAll('.species-book-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const book = btn.getAttribute('data-book');
      if (!uiState.speciesOpenBooks) {
        // Seed from the current default (first book open) so the first click
        // doesn't silently close an already-open section.
        uiState.speciesOpenBooks = {};
        const firstOpen = document.querySelector('.species-book.open .species-book-toggle');
        if (firstOpen) uiState.speciesOpenBooks[firstOpen.getAttribute('data-book')] = true;
      }
      uiState.speciesOpenBooks[book] = !uiState.speciesOpenBooks[book];
      renderStage();
    });
  });

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
  if (uiState.bgPackageMode) return renderBgPackagePicker();

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

  // Aslan (Hierate / Glorious Empire) use gender-specific background skill lists
  const isAslanHierate = !!(speciesDef && speciesDef.uses_clan_shares);
  const aslanBgMale   = ['Animals', 'Art', 'Athletics', 'Carouse', 'Drive', 'Flyer', 'Melee', 'Seafarer', 'Survival', 'Tolerance', 'Vacc Suit'];
  const aslanBgFemale = ['Admin', 'Animals', 'Art', 'Athletics', 'Electronics', 'Mechanic', 'Medic', 'Melee', 'Profession', 'Science', 'Streetwise', 'Tolerance', 'Vacc Suit'];

  let bgSkills;
  let aslanGenderNote = '';
  if (isAslanHierate && character.gender) {
    const aslanList = character.gender === 'male' ? aslanBgMale : aslanBgFemale;
    bgSkills = [...new Set([...aslanList, ...extraBgSkills])].sort();
    aslanGenderNote = `<p style="font-size:12px;color:var(--amber);margin-top:6px">★ <strong>Aslan ${character.gender === 'male' ? 'Male' : 'Female'}</strong> background skill list.</p>`;
  } else {
    bgSkills = [...new Set([...baseBgSkills, ...extraBgSkills])].sort();
  }

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
        ${aslanGenderNote || (extraBgSkills.length ? `<p style="font-size:12px;color:var(--amber);margin-top:6px">★ <strong>${speciesDef.name}</strong> trait: ${extraBgSkills.join(', ')} added to the available list (Natural Starfarers).</p>` : '')}
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

      ${isAslanHierate ? '' : `
      <div style="margin-top:24px;padding-top:18px;border-top:1px solid var(--border)">
        <p style="font-size:11px;color:var(--text-dim);margin-bottom:10px">
          — OR —<br>
          Replace education skills <em>and</em> pre-career education entirely with a <strong style="color:var(--amber)">Background Package</strong>.
          Your age advances to 22 and you proceed directly to careers.
        </p>
        <button class="btn btn-use-package" id="btn-use-bg-package">
          USE BACKGROUND PACKAGE INSTEAD
        </button>
      </div>
      `}
    </div>
  `;
}

function wireBackgroundPhase() {
  if (uiState.bgPackageMode) { wireBgPackagePicker(); return; }
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

  const usePkgBtn = document.getElementById('btn-use-bg-package');
  if (usePkgBtn) {
    usePkgBtn.addEventListener('click', () => {
      uiState.bgPackageMode = true;
      uiState.selectedBgPackage = null;
      uiState.bgPackageSkillChoices = {};
      renderStage();
    });
  }
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
// Background Package Picker (alternative to background skills)
// ============================================================

function renderBgPackagePicker() {
  const packages = Object.values(BG_PACKAGES);
  const selId    = uiState.selectedBgPackage;
  const choices  = uiState.bgPackageSkillChoices || {};

  // Stat-mod badge helper
  function fmtMods(mods) {
    const parts = Object.entries(mods || {}).map(([s, v]) => `${s}${v > 0 ? '+' : ''}${v}`);
    return parts.length ? parts.join('  ') : 'no stat changes';
  }

  const cards = packages.map(pkg => {
    const isSelected = pkg.id === selId;
    const leveledSkills = pkg.skills
      .filter(sk => sk.level > 0)
      .map(sk => {
        let n = sk.name;
        if (sk.speciality) n += ` (${sk.speciality})`;
        else if (sk.any || sk.options) n += ' (any)';
        return `${n}-${sk.level}`;
      }).join(', ');
    const zeroSkills = pkg.skills.filter(sk => sk.level === 0).map(sk => sk.name).join(', ');
    const equip = (pkg.equipment || []).filter(Boolean).join(', ');

    return `
      <div class="bg-pkg-card ${isSelected ? 'selected' : ''}" data-pkg-id="${pkg.id}">
        <div class="bg-pkg-name">${pkg.name}</div>
        <div class="bg-pkg-stats">${fmtMods(pkg.stat_mods)}</div>
        <div class="bg-pkg-skills">${leveledSkills || '—'}</div>
        ${zeroSkills ? `<div class="bg-pkg-zero">Level 0: ${zeroSkills}</div>` : ''}
        <div class="bg-pkg-benefits">Cr${(pkg.credits || 0).toLocaleString()}${equip ? ' · ' + equip : ''}</div>
      </div>`;
  }).join('');

  // Specialty pickers for the selected package
  let specialtySection = '';
  if (selId && BG_PACKAGES[selId]) {
    const anySkills = BG_PACKAGES[selId].skills.filter(sk => sk.any || (sk.options && sk.options.length));
    if (anySkills.length > 0) {
      const pickers = anySkills.map(sk => {
        const cur = choices[sk.name] || '';
        const opts = sk.options && sk.options.length ? sk.options : (CASCADE_SKILLS[sk.name] || []);
        let inputHtml;
        if (opts.length > 0) {
          const btnRow = opts.map(o =>
            `<button class="skill-chip ${cur.toLowerCase() === o.toLowerCase() ? 'selected' : ''}"
               data-pkg-spec-skill="${escapeHTML(sk.name)}"
               data-pkg-spec-value="${escapeHTML(o)}">${escapeHTML(o)}</button>`
          ).join('');
          inputHtml = `<div class="pkg-spec-chips">${btnRow}</div>`;
        } else {
          inputHtml = `<input class="pkg-spec-input" type="text"
            placeholder="Enter speciality…"
            data-pkg-spec-skill="${escapeHTML(sk.name)}"
            value="${escapeHTML(cur)}">`;
        }
        return `<div class="pkg-spec-row">
          <span class="pkg-spec-label">${escapeHTML(sk.name)}${sk.options ? ' (' + sk.options.join('/') + ')' : ' (any)'}:</span>
          ${inputHtml}
        </div>`;
      }).join('');
      specialtySection = `
        <div class="pkg-specialty-section">
          <h4>Choose specialities for this package</h4>
          ${pickers}
        </div>`;
      // All choices made?
      const allDone = anySkills.every(sk => (choices[sk.name] || '').trim());
      if (!allDone) specialtySection += ''; // confirm button stays disabled
    }
  }

  // Can we confirm?
  const anySkillsForSel = selId && BG_PACKAGES[selId]
    ? BG_PACKAGES[selId].skills.filter(sk => sk.any || (sk.options && sk.options.length))
    : [];
  const canConfirm = selId && anySkillsForSel.every(sk => (choices[sk.name] || '').trim());

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 03 — BACKGROUND PACKAGE</span></div>
    <div class="stage-content">
      <div class="phase-label">Adolescence · Pre-Career</div>
      <h2 class="phase-title">Background Package</h2>
      <p class="phase-subtitle">Pick a package that matches your upbringing. Your age advances to <strong>22</strong> and pre-career education is skipped.</p>
      <div class="bg-pkg-grid">${cards}</div>
      ${specialtySection}
      <div class="phase-actions">
        <button class="btn ghost" id="btn-pkg-back">← BACK TO SKILLS</button>
        <button class="btn primary" id="btn-pkg-confirm" ${canConfirm ? '' : 'disabled'}>
          CONFIRM PACKAGE →
        </button>
      </div>
    </div>`;
}

function wireBgPackagePicker() {
  // Package card selection
  document.querySelectorAll('[data-pkg-id]').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.dataset.pkgId;
      if (uiState.selectedBgPackage !== id) {
        uiState.selectedBgPackage = id;
        uiState.bgPackageSkillChoices = {};
      }
      renderStage();
    });
  });

  // Specialty chip selection
  document.querySelectorAll('[data-pkg-spec-skill][data-pkg-spec-value]').forEach(btn => {
    btn.addEventListener('click', () => {
      const skill = btn.dataset.pkgSpecSkill;
      const val   = btn.dataset.pkgSpecValue;
      uiState.bgPackageSkillChoices[skill] = val;
      renderStage();
    });
  });

  // Specialty free-text inputs
  document.querySelectorAll('.pkg-spec-input[data-pkg-spec-skill]').forEach(inp => {
    inp.addEventListener('input', () => {
      uiState.bgPackageSkillChoices[inp.dataset.pkgSpecSkill] = inp.value;
    });
    inp.addEventListener('change', () => renderStage());
  });

  // Back button
  const backBtn = document.getElementById('btn-pkg-back');
  if (backBtn) {
    backBtn.addEventListener('click', () => {
      uiState.bgPackageMode = false;
      uiState.selectedBgPackage = null;
      uiState.bgPackageSkillChoices = {};
      renderStage();
    });
  }

  // Confirm button
  const confirmBtn = document.getElementById('btn-pkg-confirm');
  if (confirmBtn) {
    confirmBtn.addEventListener('click', async () => {
      const pkgId   = uiState.selectedBgPackage;
      const choices = uiState.bgPackageSkillChoices || {};
      confirmBtn.disabled = true;
      confirmBtn.textContent = 'APPLYING…';
      try {
        const response = await apiCall('/api/character/background-package', {
          package_id: pkgId,
          skill_choices: choices,
        });
        uiState.bgPackageMode = false;
        uiState.selectedBgPackage = null;
        uiState.bgPackageSkillChoices = {};
        await applyResponse(response);
        renderAll();
      } catch (e) {
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'CONFIRM PACKAGE →';
        alert(e.message);
      }
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
    const levelLabel = pickLevel === 0 ? 'level 0 (your majors — you can raise them later)' : `level ${pickLevel}`;
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
    const pendingEvent11 = !!ev.pending_event11 || !!status.pending_event11;
    const pendingAslanEvent2 = !!ev.pending_aslan_event2 || !!status.pending_aslan_event2;
    const isAslanTrack = status.track === 'aslan_university';
    const pendingLifeEvent = !!ev.pending_life_event;
    const lifeEventChoiceKind = ev.life_event_choice_kind || null;
    const pendingInjury = !!ev.pending_injury;
    const injuryData = ev.injury_pending_data || character.pending_injury_choice || null;
    const nextBtn = pendingAslanEvent2
      ? `<button class="btn primary" id="btn-show-aslan-event2">RESPOND TO TEMPTATION →</button>`
      : pendingEvent11 && isAslanTrack
        ? `<button class="btn primary" id="btn-show-aslan-event11">RESPOND TO CLAN WAR →</button>`
      : pendingEvent11
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
    const pending = character.pending_life_event_choice || {};
    const kind = uiState.lastRoll.choiceKind || pending.kind;
    const { title, body, buttons } = buildLifeEventChoiceUI(kind, pending, 'precareer');

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

  // Aslan event 2 — neglectful students choice
  if (uiState.lastRoll?.type === 'precareer_aslan_event2') {
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Aslan University Event 2 — Neglectful Students</div>
        <h2 class="phase-title">A Temptation</h2>
        <p class="phase-body">A clique of students who neglect their studies attempts to draw you in. You may join them — your SOC drops to 2, but you may enter the Outlaw or Wanderer career without a qualification roll next term. Or you can stay focused on your studies.</p>
        <div class="card-grid">
          <button class="card" id="btn-aslan-ev2-join">
            <div class="card-title">Join Them</div>
            <div class="card-desc">SOC drops to 2. Free qualification for Aslan Outlaw or Wanderer in your next career term.</div>
          </button>
          <button class="card" id="btn-aslan-ev2-focus">
            <div class="card-title">Stay Focused</div>
            <div class="card-desc">Decline the distraction. No effect on your studies or SOC.</div>
          </button>
        </div>
      </div>
    `;
  }

  // Aslan event 11 — clan war choice (replaces standard draft event for Aslan University)
  if (uiState.lastRoll?.type === 'precareer_aslan_event11') {
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Aslan University Event 11 — Clan War!</div>
        <h2 class="phase-title">Your Clan Goes to War</h2>
        <p class="phase-body">Your clan is called to battle. You may flee (becoming Outcast) or enlist directly in a military career. Either way, you do not graduate.</p>
        <div class="card-grid">
          <button class="card" id="btn-aslan-ev11-outcast">
            <div class="card-title">Flee — Become Outcast</div>
            <div class="card-desc">You abandon your clan's call. You are cast out. Your next career must be Aslan Outcast.</div>
          </button>
          <button class="card" id="btn-aslan-ev11-military">
            <div class="card-title">Enlist — Military</div>
            <div class="card-desc">Enter the Aslan Military career directly. Do not graduate from Aslan University.</div>
          </button>
          <button class="card" id="btn-aslan-ev11-military-officer">
            <div class="card-title">Enlist — Military Officer</div>
            <div class="card-desc">Enter the Aslan Military Officer career directly. Do not graduate.</div>
          </button>
          <button class="card" id="btn-aslan-ev11-spacer">
            <div class="card-title">Enlist — Spacer</div>
            <div class="card-desc">Enter the Aslan Spacer career directly. Do not graduate.</div>
          </button>
          <button class="card" id="btn-aslan-ev11-space-officer">
            <div class="card-title">Enlist — Space Officer</div>
            <div class="card-desc">Enter the Aslan Space Officer career directly. Do not graduate.</div>
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

  // Graduated but lastRoll wiped (e.g. page reload) — recover any pending interactive step
  if ((stage === 'graduated' || stage === 'failed_grad') && !uiState.lastRoll) {
    if (status.pending_aslan_event2) {
      uiState.lastRoll = { type: 'precareer_aslan_event2' };
      return renderPreCareerPhase();
    }
    if (status.pending_event11 && status.track === 'aslan_university') {
      uiState.lastRoll = { type: 'precareer_aslan_event11' };
      return renderPreCareerPhase();
    }
    if (status.pending_event11) {
      uiState.lastRoll = { type: 'precareer_event11' };
      return renderPreCareerPhase();
    }
    if (status.pending_event10) {
      // Show event10 skill picker (reuse the screen; skill pool is saved in status)
      uiState.lastRoll = { type: 'precareer_event10' };
      return renderPreCareerPhase();
    }
    if (character.pending_life_event_choice) {
      const kind = character.pending_life_event_choice.kind;
      uiState.lastRoll = { type: 'precareer_life_event_choice', choiceKind: kind };
      return renderPreCareerPhase();
    }
    if ((status.skill_picks_remaining || 0) > 0) {
      uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
      uiState.lastRoll = { type: 'precareer_skill_pick' };
      return renderPreCareerPhase();
    }
    // Nothing pending — advance to career phase
    character.phase = 'career';
    saveCharacter();
    setTimeout(() => renderAll(), 0);
    return `<div class="stage-content"><p style="color:var(--text-dim)">Loading career phase…</p></div>`;
  }

  // Enrolled — always show graduate button immediately (events roll after graduation)
  if (stage === 'enrolled') {
    const track = status.track;
    const service = status.service;
    const trackName = trackDisplayName(track, service, status);
    const gradHint = trackGradHint(track);

    if (track === 'psionic_community' && status.pending_psionic_training) {
      const trainedTalents = character.psi_trained_talents || [];
      const attemptedTalents = character.psi_free_training_attempts || [];
      const talentsHTML = ['telepathy','clairvoyance','telekinesis','awareness','teleportation'].map(id => {
        const trained = trainedTalents.includes(id);
        // Each talent may only be attempted ONCE during free training (pass or fail).
        const attempted = attemptedTalents.includes(id);
        const failed = attempted && !trained;
        const label = id.charAt(0).toUpperCase() + id.slice(1);
        let mark = '', suffix = ' — free';
        if (trained) { mark = '✓ '; suffix = ''; }
        else if (failed) { mark = '✗ '; suffix = ' — failed'; }
        return `<button class="btn ${attempted ? 'ghost' : ''}" data-pc-psi-talent="${id}" ${attempted ? 'disabled' : ''}>${mark}${label}${suffix}</button>`;
      }).join('');
      return `
        <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
        <div class="stage-content">
          <div class="phase-label">Enrolled · ${trackName}</div>
          <h2 class="phase-title">Psionic Training</h2>
          <p class="phase-body">Your community will train you at no cost. Each talent may be attempted <strong>once</strong> — a failed attempt cannot be retried. Train your talents, then graduate.</p>
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
        <div class="card-title">${esc(c.name)}</div>
        <div class="card-desc">${esc(c.desc)}</div>
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
  const _pcSpeciesDef = SPECIES.find(s => s.id === character.species_id);
  const _isAslanPC = !!(_pcSpeciesDef && _pcSpeciesDef.uses_clan_shares);

  if (_isAslanPC) {
    // Aslan characters see Aslan University instead of standard University
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 03 — PRE-CAREER EDUCATION</span></div>
      <div class="stage-content">
        <div class="phase-label">Optional · Age ${character.age}</div>
        <h2 class="phase-title">Education Before Service?</h2>
        <p class="phase-subtitle">Before picking a career, you may study at an Aslan university. Or skip and go straight to the job.</p>
        <div class="card-grid">
          <button class="card" id="btn-pc-aslan-university">
            <div class="card-title">Aslan University</div>
            <div class="card-desc">EDU 6+ to qualify (DM+1 if SOC 9+), 4 years, +1 EDU on enrollment. Pick 1 gender-specific skill at level 0. Graduate for EDU+1 and DM+1 advancement in major Aslan careers. Honours adds SOC+1 and DM+2.</div>
          </button>
          <button class="card" id="btn-pc-skip">
            <div class="card-title">Skip</div>
            <div class="card-desc">Age ${character.age} and ready for the world. Go straight to the career phase.</div>
          </button>
        </div>
      </div>
    `;
  }

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
  if (track === 'aslan_university') return 'Aslan University';
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
    aslan_university: 'Roll INT 6+ to graduate (10+ for Honours). Then one Aslan education event.',
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
  const aslanUni = document.getElementById('btn-pc-aslan-university');
  if (aslanUni) aslanUni.addEventListener('click', () =>
    fireQualify('aslan_university', {}, 'Aslan University', 'EDU', 6, 4)
  );

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
          const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
          if (hasPicks) {
            uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
            uiState.lastRoll = { ...(uiState.lastRoll || {}),
              type: 'precareer_skill_pick',
              event: { ...(uiState.lastRoll?.event || {}), pending_event10: false },
            };
            renderStage();
          } else {
            uiState.lastRoll = null;
            renderAll();
          }
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
      const hasPicks = (character.pre_career_status?.skill_picks_remaining || 0) > 0;
      if (succeeded && hasPicks) {
        // Keep the graduation lastRoll context but clear the pending event11 flag
        // so the skill-pick button shows next.
        uiState.selectedPreCareerSkills = new Set(); uiState.pcSkillSpecialtyPick = null;
        uiState.lastRoll = { ...(uiState.lastRoll || {}),
          type: 'precareer_skill_pick',
          event: { ...(uiState.lastRoll?.event || {}), pending_event11: false },
        };
        renderStage();
      } else {
        uiState.lastRoll = null;
        renderAll();
      }
    } catch (e) { alert(e.message); }
  });

  // Aslan event 2: show choice screen
  const showAslanEv2Btn = document.getElementById('btn-show-aslan-event2');
  if (showAslanEv2Btn) showAslanEv2Btn.addEventListener('click', () => {
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_aslan_event2' };
    renderStage();
  });

  // Aslan event 2 choice buttons
  const aslanEv2Join = document.getElementById('btn-aslan-ev2-join');
  if (aslanEv2Join) aslanEv2Join.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/aslan-event2-choice', { choice: 'join' });
      await applyResponse(response);
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });
  const aslanEv2Focus = document.getElementById('btn-aslan-ev2-focus');
  if (aslanEv2Focus) aslanEv2Focus.addEventListener('click', async () => {
    try {
      const response = await apiCall('/api/character/pre-career/aslan-event2-choice', { choice: 'focus' });
      await applyResponse(response);
      uiState.lastRoll = null;
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Aslan event 11: show clan war screen
  const showAslanEv11Btn = document.getElementById('btn-show-aslan-event11');
  if (showAslanEv11Btn) showAslanEv11Btn.addEventListener('click', () => {
    uiState.lastRoll = { ...uiState.lastRoll, type: 'precareer_aslan_event11' };
    renderStage();
  });

  // Aslan event 11 choice buttons
  const _aslanEv11Choices = {
    'btn-aslan-ev11-outcast':         'outcast',
    'btn-aslan-ev11-military':        'aslan_military',
    'btn-aslan-ev11-military-officer':'aslan_military_officer',
    'btn-aslan-ev11-spacer':          'aslan_spacer',
    'btn-aslan-ev11-space-officer':   'aslan_space_officer',
  };
  Object.entries(_aslanEv11Choices).forEach(([btnId, choice]) => {
    const btn = document.getElementById(btnId);
    if (btn) btn.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/pre-career/aslan-event11-choice', { choice });
        await applyResponse(response);
        uiState.lastRoll = null;
        renderAll();
      } catch (e) { alert(e.message); }
    });
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
// PHASE 3b: Aslan Hierate Background Setup
// ============================================================

function renderAslanSetupPhase() {
  const setup = character.aslan_setup_status || {};
  const setupPhase = setup.phase || null;
  const sp = SPECIES.find(s => s.id === character.species_id) || null;
  const spName = sp ? sp.name : 'Aslan';

  // Intermediate result display — show roll outcome before advancing to next step
  if (uiState.aslanRollResult) {
    const res = uiState.aslanRollResult;
    let resultHTML = '';

    if (res.type === 'clan') {
      if (res.fixed_clan) {
        // Glorious Empire — no dice, auto-assigned
        resultHTML = `
          <div class="roll-result-block">
            <div class="roll-result-label">→ <strong>${res.clan_type}</strong></div>
            <div class="roll-result-note">All Glorious Empire Aslan are from the Tokouea'we clan (DM±0 to Ancestral Deeds).</div>
          </div>`;
      } else {
        const r = res.roll;
        resultHTML = `
          <div class="roll-result-block">
            <div class="roll-result-dice">1D = <strong>${r.raw_total}</strong></div>
            <div class="roll-result-label">→ <strong>${res.clan_type}</strong></div>
            ${res.dm_ancestral_deeds > 0 ? `<div class="roll-result-note">DM+${res.dm_ancestral_deeds} to Ancestral Deeds</div>` : ''}
          </div>`;
      }
    } else if (res.type === 'ancestry') {
      const ar = res.ancestral_roll;
      const dm = ar.modifier || 0;
      resultHTML = `
        <div class="roll-result-block">
          <div class="roll-result-label">Ancestral Deeds</div>
          <div class="roll-result-dice">1D${dm > 0 ? `+${dm}` : ''} = <strong>${ar.total}</strong> → ${res.ancestral_result.label || ''}</div>
          ${(res.past_deeds_rolls || []).map(p => `
            <div class="roll-result-dice">${p.who}: 2D = <strong>${p.roll.total}</strong>
              → ${p.label}
              ${typeof p.territory_change === 'number' && p.territory_change !== 0 ? ` (territory ${p.territory_change > 0 ? '+' : ''}${p.territory_change})` : ''}
              ${p.territory_change === 'lose_all' ? ' (lose all territory)' : ''}
            </div>`).join('')}
          <div class="roll-result-label">→ Ancestral Territory: <strong>${res.ancestral_territory}</strong>. TER set to <strong>${res.ter_set_to}</strong>.</div>
          ${res.stat_bonus_note ? `<div class="roll-result-note">${res.stat_bonus_note}</div>` : ''}
          ${(res.bonus_notes || []).map(n => `<div class="roll-result-note">${n}</div>`).join('')}
        </div>`;
    } else if (res.type === 'family') {
      const r = res.roll;
      resultHTML = `
        <div class="roll-result-block">
          <div class="roll-result-dice">2D = <strong>${r.total}</strong> (${r.dice.join(', ')})</div>
          <div class="roll-result-label">→ <strong>${res.family_position}</strong></div>
          <div class="roll-result-note">${res.inherits_territory
            ? 'You inherit the Ancestral Territory. TER = ' + res.ter
            : 'You do not inherit territory. TER reset to 0.'}</div>
        </div>`;
    } else if (res.type === 'rite') {
      const r = res.roll;
      const doublesHTML = res.is_doubles && res.doubles_result ? `
        <div class="roll-result-label" style="color:var(--danger)">⚡ DOUBLES — ${res.doubles_key}</div>
        <div class="roll-result-note" style="font-style:normal;font-size:13px">${res.doubles_result.label}</div>
        ${(res.doubles_applied || []).map(a => `<div class="roll-result-note" style="color:var(--amber)">→ ${a}</div>`).join('')}
      ` : '';
      resultHTML = `
        <div class="roll-result-block">
          <div class="roll-result-dice">2D = <strong>${r.total}</strong> (${r.dice.join(', ')})</div>
          <div class="roll-result-label">Rite Score: <strong>${res.rite_score}</strong></div>
          ${doublesHTML}
        </div>`;
    }

    return `
      <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND — RESULT</span></div>
      <div class="stage-content">
        <div class="phase-label">Roll Result</div>
        <div class="phase-title">${res.title}</div>
        ${resultHTML}
        <div class="phase-actions">
          <button class="btn primary" id="btn-aslan-result-continue">CONTINUE →</button>
        </div>
      </div>`;
  }

  // If setup hasn't been initialised yet, show Begin Setup button
  if (!setupPhase) {
    return `
      <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND SETUP</span></div>
      <div class="stage-content">
        <div class="phase-label">Background Setup</div>
        <div class="phase-title">${spName}</div>
        <p class="phase-body">Aslan characters have a unique background process: clan, ancestry, family, and the Rite of Passage all shape who you are before careers begin.</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-aslan-begin">BEGIN SETUP →</button>
        </div>
      </div>`;
  }

  // Gender picker
  if (setupPhase === 'gender') {
    return `
      <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND — GENDER</span></div>
      <div class="stage-content">
        <div class="phase-label">Step 1 — Gender</div>
        <div class="phase-title">Choose Your Gender</div>
        <p class="phase-body">Aslan society is strongly gendered. Males are warriors, diplomats, and leaders; females are scientists, merchants, and administrators. Your gender determines which careers and assignments you may enter.</p>
        <p class="phase-body">By Aslan biology, approximately three females are born for every male. You may choose freely.</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-aslan-male" data-gender="male">♂ MALE</button>
          <button class="btn ghost" id="btn-aslan-female" data-gender="female">♀ FEMALE</button>
        </div>
      </div>`;
  }

  // Clan roll
  if (setupPhase === 'clan') {
    const genderLabel = character.gender === 'male' ? 'Male' : 'Female';
    const isGE = character.species_id === 'glorious_empire_aslan';
    if (isGE) {
      return `
        <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND — CLAN</span></div>
        <div class="stage-content">
          <div class="phase-label">Step 2 — Clan Origin</div>
          <div class="phase-title">Clan Origin</div>
          <p class="phase-body">Gender: <strong>${genderLabel}</strong>. All Glorious Empire Aslan are from the <strong>Tokouea'we clan</strong> — no roll is required. The Tokouea'we gives no positive DM on Ancestral Deeds.</p>
          <p class="phase-body">Instead, males with STR 10+ and females with INT 8+ receive DM+1 on the Ancestral Deeds roll.</p>
          <div class="phase-actions">
            <button class="btn primary" id="btn-aslan-roll-clan">ASSIGN CLAN →</button>
          </div>
        </div>`;
    }
    return `
      <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND — CLAN</span></div>
      <div class="stage-content">
        <div class="phase-label">Step 2 — Clan Origin</div>
        <div class="phase-title">Clan Origin</div>
        <p class="phase-body">Gender: <strong>${genderLabel}</strong>. Now determine your clan. Roll 1D to find whether you come from a Minor Clan or one of the 29 Great Clans of the Tlaukhu (Major Clan, DM+1 to Ancestral Deeds).</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-aslan-roll-clan">ROLL CLAN (1D)</button>
        </div>
      </div>`;
  }

  // Ancestry roll
  if (setupPhase === 'ancestry') {
    const clanLabel = setup.clan_type || '?';
    const clanDm = setup.clan_dm_ancestral_deeds || 0;
    const isGE = character.species_id === 'glorious_empire_aslan';
    let dmNote = '';
    if (isGE) {
      const isMale = character.gender === 'male';
      const statName = isMale ? 'STR' : 'INT';
      const statMin  = isMale ? 10 : 8;
      const statVal  = (character.characteristics || {})[statName] || 0;
      const qualifies = statVal >= statMin;
      dmNote = `<p class="phase-body">GE bonus: ${statName} ${statVal} ${qualifies ? `≥ ${statMin} — <strong>DM+1 applies</strong>` : `< ${statMin} — no bonus DM`}.</p>`;
    } else if (clanDm > 0) {
      dmNote = ``;
    }
    return `
      <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND — ANCESTRY</span></div>
      <div class="stage-content">
        <div class="phase-label">Step 3 — Ancestral Territory</div>
        <div class="phase-title">Ancestral Territory</div>
        <p class="phase-body">Clan: <strong>${clanLabel}</strong>${clanDm > 0 ? ` (DM+${clanDm} to Ancestral Deeds)` : ''}.</p>
        ${dmNote}
        <p class="phase-body">Roll 1D for Ancestral Deeds, then twice on Past Deeds (2D each: once for grandfather, once for father). The total becomes your starting TER (Ancestral Territory).</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-aslan-roll-ancestry">ROLL ANCESTRY (1D + 2×2D)</button>
        </div>
      </div>`;
  }

  // Family inheritance
  if (setupPhase === 'family') {
    const terr = setup.ancestral_territory || 0;
    return `
      <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND — FAMILY</span></div>
      <div class="stage-content">
        <div class="phase-label">Step 4 — Family Position</div>
        <div class="phase-title">Family Position</div>
        <p class="phase-body">Ancestral Territory: <strong>${terr}</strong> (TER set to ${terr}).</p>
        <p class="phase-body">Roll 2D to determine your birth order. Only the first son / eldest daughter inherits the family's full Ancestral Territory. Others have TER reset to 0 and must earn their own standing.</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-aslan-roll-family">ROLL FAMILY POSITION (2D)</button>
        </div>
      </div>`;
  }

  // Rite of Passage
  if (setupPhase === 'rite') {
    const pos = setup.family_position || '?';
    const inherits = setup.inherits_territory;
    const genderLabel = character.gender === 'male' ? 'male' : 'female';
    const riteDesc = character.gender === 'male'
      ? 'Roll 2D (= X). Count how many of STR, DEX, END, INT, EDU, SOC exceed X (= Y). Final score = X + Y.'
      : 'Roll 2D; score +2 for each of INT, EDU, SOC that exceeds the roll.';
    return `
      <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND — RITE OF PASSAGE</span></div>
      <div class="stage-content">
        <div class="phase-label">Step 5 — Rite of Passage</div>
        <div class="phase-title">Akhuaeuhrekhyeh</div>
        <p class="phase-body">Birth order: <strong>${pos}</strong> ${inherits ? '(inherits territory)' : '(no inheritance)'}. TER = ${(character.extra_characteristics && character.extra_characteristics.TER != null) ? character.extra_characteristics.TER : 0}.</p>
        <p class="phase-body">At age 15, all Aslan undergo the Rite of Passage. As a ${genderLabel}: ${riteDesc}</p>
        <p class="phase-body">If doubles are rolled, a special Rite Event occurs. The resulting <strong>Rite Score</strong> is used as a DM for career qualification.</p>
        <div class="phase-actions">
          <button class="btn primary" id="btn-aslan-roll-rite">ROLL RITE OF PASSAGE (2D)</button>
        </div>
      </div>`;
  }

  // Done — shouldn't normally render here (phase transitions to 'career')
  return `
    <div class="panel-header"><span class="led"></span><span>ASLAN BACKGROUND — COMPLETE</span></div>
    <div class="stage-content">
      <div class="phase-label">Background Complete</div>
      <p class="phase-body">Background setup complete. Rite Score: <strong>${setup.rite_score || 0}</strong>.</p>
      <div class="phase-actions">
        <button class="btn primary" id="btn-aslan-continue">CONTINUE TO CAREERS →</button>
      </div>
    </div>`;
}

function wireAslanSetupPhase() {
  // Result continue button (shown after each roll)
  document.getElementById('btn-aslan-result-continue')?.addEventListener('click', () => {
    uiState.aslanRollResult = null;
    renderAll();
  });

  // Begin setup button
  document.getElementById('btn-aslan-begin')?.addEventListener('click', async () => {
    try {
      const data = await apiCall('/api/character/aslan/begin-setup', {});
      character = data.character;
      saveCharacter();
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Gender buttons
  document.querySelectorAll('[data-gender]').forEach(btn => {
    btn.addEventListener('click', async () => {
      try {
        const gender = btn.dataset.gender;
        const data = await apiCall('/api/character/aslan/choose-gender', { gender });
        character = data.character;
        saveCharacter();
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  // Clan roll
  document.getElementById('btn-aslan-roll-clan')?.addEventListener('click', async () => {
    try {
      const data = await apiCall('/api/character/aslan/roll-clan', {});
      character = data.character;
      saveCharacter();
      uiState.aslanRollResult = { type: 'clan', title: 'Clan Origin', ...data };
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Ancestry roll
  document.getElementById('btn-aslan-roll-ancestry')?.addEventListener('click', async () => {
    try {
      const data = await apiCall('/api/character/aslan/roll-ancestry', {});
      character = data.character;
      saveCharacter();
      uiState.aslanRollResult = { type: 'ancestry', title: 'Ancestral Territory', ...data };
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Family roll
  document.getElementById('btn-aslan-roll-family')?.addEventListener('click', async () => {
    try {
      const data = await apiCall('/api/character/aslan/roll-family', {});
      character = data.character;
      saveCharacter();
      uiState.aslanRollResult = { type: 'family', title: 'Family Position', ...data };
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Rite roll
  document.getElementById('btn-aslan-roll-rite')?.addEventListener('click', async () => {
    try {
      const data = await apiCall('/api/character/aslan/roll-rite', {});
      character = data.character;
      saveCharacter();
      uiState.aslanRollResult = { type: 'rite', title: 'Rite of Passage — Akhuaeuhrekhyeh', ...data };
      renderAll();
    } catch (e) { alert(e.message); }
  });

  // Continue (fallback if somehow at done state)
  document.getElementById('btn-aslan-continue')?.addEventListener('click', () => {
    character.phase = 'career';
    saveCharacter();
    renderAll();
  });
}

// ============================================================
// ZHODANI PSIONIC TRAINING PHASE
// ============================================================

function renderZhodaniTrainingPhase() {
  const sp = SPECIES.find(s => s.id === character.species_id) || {};
  const isZhodani = character.species_id === 'zhodani';
  const spName = sp.name || 'Unknown Species';
  const training = sp.psionic_training_table || {};
  const talents = training.talents || [];
  const autoTalents = training.auto_talents || [];
  const requiredNext = training.required_next || null; // { name, level }
  const soc = character.characteristics?.SOC ?? 0;
  const zclass = isZhodani ? (soc >= 11 ? 'Noble' : 'Intendant') : null;
  const psi = character.psi ?? 0;
  const psiDm = charDM(psi);

  // Parse trained/failed from psi_trained_talents
  const trainedList = character.psi_trained_talents || [];
  const gainedSet = new Set(trainedList.filter(t => !t.endsWith('/failed')));
  const failedSet = new Set(trainedList.filter(t => t.endsWith('/failed')).map(t => t.replace('/failed', '')));
  const attemptsCount = trainedList.length;

  // required_next: has it been attempted yet?
  const reqAttempted = requiredNext
    ? (gainedSet.has(requiredNext.name) || failedSet.has(requiredNext.name))
    : true; // no constraint if no required_next

  const rows = talents.map(t => {
    const gained = gainedSet.has(t.name);
    const failed = failedSet.has(t.name);
    const attempted = gained || failed;
    const nextCumDm = -attemptsCount;
    const totalDm = psiDm + t.dm + nextCumDm;
    const dmLabel = `${totalDm >= 0 ? '+' : ''}${totalDm}`;
    const dmBreak = `PSI DM${psiDm >= 0 ? '+' : ''}${psiDm}, talent DM${t.dm >= 0 ? '+' : ''}${t.dm}, cumulative DM${nextCumDm >= 0 ? '+' : ''}${nextCumDm}`;
    let statusBadge = '';
    if (gained) statusBadge = `<span class="badge badge-success">GAINED</span>`;
    else if (failed) statusBadge = `<span class="badge badge-danger">FAILED</span>`;
    // Block non-required talents until required_next has been attempted
    const isReqNext = requiredNext && t.name.toLowerCase() === requiredNext.name.toLowerCase();
    const blocked = !attempted && requiredNext && !isReqNext && !reqAttempted;
    const reqNote = isReqNext && !attempted
      ? `<span class="empty" style="font-size:11px"> (must attempt first)</span>` : '';
    const successNote = isReqNext && requiredNext?.level > 0
      ? ` — gains at level ${requiredNext.level} if successful` : '';

    return `
      <tr class="${attempted ? 'attempted' : blocked ? 'locked' : ''}">
        <td><strong>${esc(t.name)}</strong>${reqNote}${esc(successNote)}</td>
        <td class="text-center">${t.dm >= 0 ? '+' : ''}${t.dm}</td>
        <td class="text-center" title="${dmBreak}">2D${dmLabel} vs 8+</td>
        <td>${statusBadge}</td>
        <td>
          ${!attempted && !blocked
            ? `<button class="btn btn-sm primary" data-train-talent="${escapeAttr(t.name)}">ATTEMPT</button>`
            : blocked ? `<span class="empty" style="font-size:11px">attempt ${esc(requiredNext.name)} first</span>`
            : ''}
        </td>
      </tr>`;
  }).join('');

  // Auto-talents display
  const autoHTML = autoTalents.length ? `
    <div class="event-box" style="border-color:var(--success,#7fd87f);margin-bottom:12px">
      <span class="event-label" style="color:var(--success,#7fd87f)">AUTO-GRANTED</span>
      ${autoTalents.map(a => `<strong>${esc(a.name)} ${a.level}</strong>`).join(', ')} — automatically granted by species.
    </div>` : '';

  const lastResult = uiState.zhodaniTrainResult || null;
  const gainedLevel = lastResult?.success_level ?? 0;
  const resultHTML = lastResult ? `
    <div class="roll-result-block">
      <div class="roll-result-label">${esc(lastResult.talent)} — ${lastResult.succeeded ? '✓ Gained!' : '✗ Failed'}</div>
      <div class="roll-result-dice">2D${lastResult.total_dm >= 0 ? '+' : ''}${lastResult.total_dm} = <strong>${lastResult.roll.total}</strong> vs 8+</div>
      ${lastResult.succeeded ? `<div class="roll-result-note">Added <strong>${esc(lastResult.talent)}</strong> at level ${gainedLevel}.</div>` : ''}
    </div>` : '';

  const phaseTitle = isZhodani ? `Psionic Talent Training — ${zclass}` : `Psionic Talent Training`;
  const phaseDesc = isZhodani
    ? `Zhodani ${zclass}s undergo psionic training before entering careers.
       For each talent, roll 2D + PSI DM + Talent DM − (checks made so far) vs 8+.
       On success, you gain the talent at level 0. You may attempt any or all talents in any order.`
    : `${esc(spName)} characters undergo psionic training before careers.
       ${requiredNext ? `<strong>${esc(requiredNext.name)}</strong> must be attempted first (gained at level ${requiredNext.level} if successful). ` : ''}
       Additional talents are gained at level 0 if the check succeeds. You may attempt as many as you wish.`;

  return `
    <div class="panel-header"><span class="led"></span><span>PSIONIC TALENT TRAINING</span></div>
    <div class="stage-content">
      <div class="phase-label">Pre-Career</div>
      <div class="phase-title">${phaseTitle}</div>
      <p class="phase-body">${phaseDesc}</p>
      ${autoHTML}
      <div class="phase-stats-row">
        <span>PSI: <strong>${psi}</strong></span>
        <span>PSI DM: <strong>${psiDm >= 0 ? '+' : ''}${psiDm}</strong></span>
        <span>Attempts so far: <strong>${attemptsCount}</strong></span>
        <span>Cumulative DM now: <strong>${attemptsCount > 0 ? `-${attemptsCount}` : '0'}</strong></span>
      </div>
      ${resultHTML}
      <table class="skills-table" style="margin:12px 0">
        <thead><tr>
          <th>Talent</th><th class="text-center">Talent DM</th><th class="text-center">Roll Required</th><th>Status</th><th></th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div class="phase-actions">
        <button class="btn secondary" id="btn-zhodani-finish-training">FINISH TRAINING →</button>
      </div>
    </div>`;
}

function wireZhodaniTrainingPhase() {
  document.querySelectorAll('[data-train-talent]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const talentName = btn.dataset.trainTalent;
      try {
        const data = await apiCall('/api/character/zhodani/train-talent', { talent_name: talentName });
        character = data.character;
        const total_dm = (data.psi_dm || 0) + (data.talent_dm || 0) + (data.cumulative_dm || 0);
        uiState.zhodaniTrainResult = {
          talent: talentName,
          succeeded: data.succeeded,
          roll: data.roll,
          total_dm,
        };
        saveCharacter();
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  document.getElementById('btn-zhodani-finish-training')?.addEventListener('click', async () => {
    try {
      const data = await apiCall('/api/character/zhodani/finish-training', {});
      character = data.character;
      uiState.zhodaniTrainResult = null;
      saveCharacter();
      renderAll();
    } catch (e) { alert(e.message); }
  });
}

// ============================================================
// PHASE 4: Career Loop
// ============================================================

function renderCareerPhase() {
  if (uiState.careerPackageMode) {
    return uiState.careerPackagePhase === 'finalising'
      ? renderCareerPackageFinalising()
      : renderCareerPackagePicker();
  }

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
  // Careers the character was ejected from via mishap (survived=false or mishap set).
  // These are NOT hidden, just flagged so the player knows to expect difficulty.
  const ejectedCareerIds = new Set(
    (character.career_history || [])
      .filter(t => t.survived === false || (t.mishap && t.mishap.length > 0))
      .map(t => t.career_id)
      .filter(id => !banned.has(id))
  );
  const soc = character.society_id || 'third_imperium';
  const speciesId = character.species_id || null;
  const speciesDef = SPECIES.find(s => s.id === speciesId) || null;
  const isCetacean = speciesId === 'dolphin' || speciesId === 'uplifted_orca';
  // Does this character have Vacc Suit skill at any level?
  const hasVaccSuit = (character.skills || []).some(s => (s.name || '').toLowerCase() === 'vacc suit' && s.level >= 1);
  // blocked_careers applies to ALL species (cetaceans use it too, plus have the vacc suit gate below)
  const cetaceanBlockedCareers = new Set((speciesDef && speciesDef.blocked_careers) || []);

  // Aslan characters (uses_clan_shares) must only see Aslan-specific careers.
  // GE Aslan see careers tagged glorious_empire (and shared ones tagged aslan_hierate).
  // Hierate Aslan see careers tagged aslan_hierate only.
  const isAslan = !!(speciesDef && speciesDef.uses_clan_shares);
  const isGEAslan = speciesId === 'glorious_empire_aslan';
  const aslanSocietyTag = isGEAslan ? 'glorious_empire' : 'aslan_hierate';

  // K'kree characters (uses_kkree_family) must only see K'kree careers (two_thousand_worlds tag).
  const isKkree = !!(speciesDef && speciesDef.uses_kkree_family);

  // Hiver characters (hiver_species) must only see Hiver careers (hiver_federation tag).
  const isHiver = !!(speciesDef && speciesDef.hiver_species);

  // Droyne characters (droyne_caste_system) must only see Droyne careers (droyne careers have allowed_species: ["droyne"]).
  const isDroyne = !!(speciesDef && speciesDef.droyne_caste_system);

  const mustBeCore = !!(character.next_career_must_be_core);
  // Species career whitelist (e.g. Floriani Feskal/Barnai)
  const speciesAllowedCareers = (speciesDef && speciesDef.allowed_career_ids && speciesDef.allowed_career_ids.length)
    ? new Set(speciesDef.allowed_career_ids)
    : null;

  const careerList = forcedId
    ? CAREERS.filter(c => c.id === forcedId)
    : CAREERS.filter(c => {
        if (banned.has(c.id)) return false;
        // Species career whitelist
        if (speciesAllowedCareers && !speciesAllowedCareers.has(c.id)) return false;
        // Ihatei restriction: only core rulebook careers (no societies, or includes third_imperium)
        if (mustBeCore) {
          const socs = c.societies || [];
          const isCore = socs.length === 0 || socs.includes('third_imperium');
          if (!isCore) return false;
        }
        // Aslan: only show careers whitelisted for this Aslan society tag
        if (isAslan && !(c.societies && c.societies.includes(aslanSocietyTag))) return false;
        // K'kree: only show careers tagged two_thousand_worlds
        if (isKkree && !(c.societies && c.societies.includes('two_thousand_worlds'))) return false;
        // Hiver: only show careers tagged hiver_federation
        if (isHiver && !(c.societies && c.societies.includes('hiver_federation'))) return false;
        // Droyne: only show careers that allow droyne species (droyne_caste_system careers)
        if (isDroyne && !(c.allowed_species && c.allowed_species.includes('droyne'))) return false;
        // "societies" = whitelist: only show for these societies
        // (Aslan, K'kree, Hiver, and Droyne characters are already filtered above — skip the generic check)
        if (!isAslan && !isKkree && !isHiver && !isDroyne && c.societies && c.societies.length > 0 && !c.societies.includes(soc)) return false;
        // "blocked_societies" = blacklist: hide for these societies
        if (c.blocked_societies && c.blocked_societies.includes(soc)) return false;
        // "allowed_species" / "blocked_species" — don't hard-hide; show as locked cards instead.
        // Species blocked_careers: hide for any species that lists them (not just cetaceans)
        if (cetaceanBlockedCareers.has(c.id)) return false;
        // Cetacean species: non-cetacean-specific careers require Vacc Suit first
        if (isCetacean && (!c.allowed_species || c.allowed_species.length === 0) && !hasVaccSuit) return false;
        // Semi-careers with a source-career requirement (e.g. Imperial Guard, INI):
        // only show when the character is currently serving in a qualifying career.
        if (c.requires_source_career) {
          const curCareerId = character.current_term?.career_id || null;
          if (!curCareerId || !c.requires_source_career.includes(curCareerId)) return false;
          // Some semi-careers (e.g. Imperial Guard) also require a promotion in the current term
          if (c.requires_advancement && !character.current_term?.advanced) return false;
        }
        return true;
      });
  const forcedCareerName = forcedId ? (CAREERS.find(c => c.id === forcedId)?.name || forcedId.toUpperCase()) : null;
  const forcedBanner = forcedId ? `
    <p class="phase-body" style="color:var(--danger);font-weight:bold">
      ⚠ You must enter the <strong>${forcedCareerName}</strong> career this term — this is mandatory.
    </p>` : '';
  const coreBanner = mustBeCore && !forcedId ? `
    <p class="phase-body" style="color:var(--amber);font-weight:bold">
      ⚠ Ihatei restriction: you must qualify for a Core Rulebook career this term (alien/society-specific careers are hidden).
    </p>` : '';
  const bannedBanner = banned.size && !forcedId ? `
    <p class="phase-body" style="color:var(--amber-dim);font-size:11px">
      Banned from re-entry: ${[...banned].map(id => id.toUpperCase()).join(', ')}
    </p>` : '';
  const speciesCareerBanner = speciesAllowedCareers && !forcedId ? `
    <p class="phase-body" style="color:var(--amber);font-size:11px">
      ⚠ ${esc(speciesDef.name)} career restriction: only permitted careers are shown.
    </p>` : '';
  const vaccLockBanner = isCetacean && !hasVaccSuit && !forcedId ? `
    <p class="phase-body" style="color:var(--amber);font-size:11px">
      🐬 Cetacean restriction: core careers are unavailable until you have the <strong>Vacc Suit</strong> skill.
      Gain it through a cetacean career first, then core careers will unlock.
    </p>` : '';

  // Aslan rite-of-passage gating: careers with RITE_OF_PASSAGE qualification
  // are locked if character's rite score is below the target.
  const riteScore = isAslan
    ? ((character.aslan_setup_status || {}).rite_score || 0)
    : null;

  const cards = careerList.map(c => {
    const isComplete = c.complete;
    const qual = c.qualification || {};
    let qualText;
    if (qual.automatic) {
      qualText = 'AUTO';
    } else if (qual.characteristic === 'DEX_OR_INT') {
      qualText = `DEX or INT ${qual.target}+`;
    } else if (qual.characteristic === 'RITE_OF_PASSAGE') {
      qualText = `RITE ${qual.target}+`;
    } else {
      qualText = `${qual.characteristic} ${qual.target}+`;
    }

    // Rite-lock: Aslan career needs RITE_OF_PASSAGE and character score is below target
    const riteLocked = riteScore !== null
      && qual.characteristic === 'RITE_OF_PASSAGE'
      && riteScore < qual.target;

    const classes = ['card'];
    if (!isComplete) classes.push('partial');

    if (riteLocked) {
      return `
        <div class="card rite-locked" title="Requires Rite Score ${qual.target}+ (yours: ${riteScore})">
          <div class="card-title">${esc(c.name)}</div>
          <div class="card-meta">RITE ${qual.target}+ · SCORE ${qual.target} REQUIRED (YOURS: ${riteScore})</div>
          <div class="card-desc">${esc(c.description)}</div>
        </div>
      `;
    }
    const wasEjected = ejectedCareerIds.has(c.id);

    // Species lock: blocked_species lists this character, or allowed_species excludes them
    const speciesBlocked = (c.blocked_species && c.blocked_species.includes(speciesId));
    const speciesNotAllowed = (c.allowed_species && c.allowed_species.length > 0 && (!speciesId || !c.allowed_species.includes(speciesId)));
    const speciesLocked = speciesBlocked || speciesNotAllowed;
    if (speciesLocked) {
      const lockReason = c.species_lock_reason ||
        (speciesBlocked ? `Not available to this species` : `Restricted to specific species`);
      return `
        <div class="card species-locked" title="${esc(lockReason)}">
          <div class="card-title">${esc(c.name)} <span class="species-lock-flag">✕ RESTRICTED</span></div>
          <div class="card-meta">${qualText}</div>
          <div class="card-desc" style="color:var(--fg-dim)">${esc(lockReason)}</div>
        </div>
      `;
    }

    if (wasEjected) classes.push('career-ejected');

    // INI return-to-Navy banner: shown on Navy cards when ini_can_return_to_navy is set
    let iniReturnBadge = '';
    const _INI_NAVY_IDS = new Set(['navy','confederation_navy','vargr_navy','zhodani_navy']);
    if (_INI_NAVY_IDS.has(c.id) && character.ini_can_return_to_navy) {
      const _iniSrc = character.ini_source_career_id || '';
      if (_iniSrc === c.id || _INI_NAVY_IDS.has(_iniSrc)) {
        iniReturnBadge = `
          <div style="margin-top:6px;font-size:10px;font-weight:600;color:var(--success,#7fd87f)">
            ← INI RETURN — Auto-qualify at held rank (no roll required)
          </div>`;
      }
    }

    // Imperial Guard: show qualification DM details on its card (card only appears when source career + promotion met)
    let igEligBadge = '';
    if (c.id === 'imperial_guard') {
      const _str = character.characteristics?.STR ?? 0;
      const _end = character.characteristics?.END ?? 0;
      const _soc = character.characteristics?.SOC ?? 0;
      const _hasMishap = (character.term_history || []).some(h => h.mishap && h.mishap.trim());
      const _hasVacc = (character.skills || []).some(s => s.name?.toLowerCase() === 'vacc suit' && s.level >= 1);
      const igDMs = [
        _str >= 10 || _end >= 10 ? `DM+1 (STR/END 10+)` : null,
        _end >= 10 ? `DM+1 (END 10+)` : null,
        _soc >= 9  ? `DM+1 (SOC 9+)`  : null,
      ].filter(Boolean);
      const igWarnings = [
        _hasMishap ? '⚠ Mishap on record — qualification blocked' : null,
        !_hasVacc  ? '⚠ Vacc Suit 1+ required — qualification blocked' : null,
        (_str < 10 && _end < 10) ? '⚠ STR or END 10+ required — qualification blocked' : null,
      ].filter(Boolean);
      igEligBadge = `
        <div class="ig-elig" style="margin-top:6px;font-size:10px;line-height:1.6;color:var(--fg-dim)">
          END 11+ · ${igDMs.length ? igDMs.join(' · ') : 'no active DMs'}
          ${igWarnings.map(w => `<div style="color:var(--danger);margin-top:1px">${escapeHTML(w)}</div>`).join('')}
        </div>`;
    }

    // INI: show qualification DM details (card only appears when currently in Navy)
    let iniEligBadge = '';
    if (c.id === 'ini') {
      const _int = character.characteristics?.INT ?? 0;
      const _edu = character.characteristics?.EDU ?? 0;
      const iniDMs = [
        _int >= 9 ? `DM+1 (INT 9+)` : null,
        _edu >= 9 ? `DM+1 (EDU 9+)` : null,
      ].filter(Boolean);
      iniEligBadge = `
        <div class="ig-elig" style="margin-top:6px;font-size:10px;line-height:1.6;color:var(--fg-dim)">
          INT 7+ · ${iniDMs.length ? iniDMs.join(' · ') : 'no active DMs'}
          <div style="margin-top:1px">Failure is not permanent — posting can be re-requested next term.</div>
        </div>`;
    }

    return `
      <button class="${classes.join(' ')}" data-career="${c.id}">
        <div class="card-title">${esc(c.name)}${wasEjected ? ' <span class="ejected-flag">⚠ EJECTED</span>' : ''}</div>
        <div class="card-meta">${qualText}${qual.auto_qualify_if?.SOC ? ` · AUTO@SOC≥${qual.auto_qualify_if.SOC.replace('>=','')}` : ''}${riteScore !== null && qual.characteristic === 'RITE_OF_PASSAGE' ? ` · YOUR SCORE: ${riteScore}` : ''}</div>
        <div class="card-desc">${esc(c.description)}</div>
        ${igEligBadge}${iniEligBadge}${iniReturnBadge}
      </button>
    `;
  }).join('');

  const careerPackageBanner = (character.total_terms === 0 && !forcedId && Object.keys(CAREER_PACKAGES).length > 0) ? `
    <div class="cp-banner">
      <div class="cp-banner-text">
        <strong>Career Package available</strong> — skip normal careers and take a pre-built career package instead.
        You will not be able to take any other jobs, but gain a complete set of skills and benefits in one step.
      </div>
      <button class="btn ghost btn-use-career-package">USE CAREER PACKAGE INSTEAD →</button>
    </div>` : '';

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 04 — CAREER SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">Term ${character.total_terms + 1} · Age ${character.age}</div>
      <h2 class="phase-title">Choose a Career</h2>
      ${forcedBanner}
      ${coreBanner}
      ${speciesCareerBanner}
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

      ${careerPackageBanner}

      ${character.total_terms > 0 ? `
        <div class="phase-actions">
          <button class="btn" id="btn-finish-creation">FINISH CHARACTER CREATION →</button>
        </div>
      ` : ''}
    </div>
  `;
}

// ============================================================
// Career Package — render helpers
// ============================================================

function _cpAnySkills(pkg) {
  // Return package skills that require specialty input (level >= 1 and "any": true)
  return (pkg.skills || []).filter(sk => sk.any && sk.level >= 1);
}

function _cpEligibleBoostSkills(pkg, forMax4) {
  // Skills eligible for finalising boost options (level 1+ in package)
  const minLevel = forMax4 ? 1 : 0;
  return (pkg.skills || []).filter(sk => sk.level > minLevel || (!forMax4 && sk.level >= 0));
}

function _buildSkillLabel(sk, skillChoices) {
  const key  = sk.key || sk.name;
  const spec = sk.speciality || (sk.any ? skillChoices[key] : null);
  return spec ? `${sk.name} (${spec}) ${sk.level}` : `${sk.name} ${sk.level}`;
}

function renderCareerPackagePicker() {
  const packages = Object.values(CAREER_PACKAGES.packages || {});
  const selId    = uiState.selectedCareerPackage;
  const choices  = uiState.careerPackageSkillChoices;

  const cards = packages.map(pkg => {
    const isSel  = pkg.id === selId;
    const minSoc = pkg.min_soc;
    const socBlock = minSoc && character.characteristics.SOC < minSoc;
    const statMods = Object.entries(pkg.stat_mods || {})
      .map(([s, v]) => `${s}${v > 0 ? '+' : ''}${v}`).join('  ') || '—';
    const rankStr = pkg.rank_title ? `Rank ${pkg.rank} · ${pkg.rank_title}` : (pkg.rank ? `Rank ${pkg.rank}` : '—');
    const benefitBits = [];
    if (pkg.rank) benefitBits.push(rankStr);
    if (pkg.credits) benefitBits.push(`Cr${pkg.credits.toLocaleString()}`);
    if (pkg.contacts) benefitBits.push(`${pkg.contacts} Contact${pkg.contacts > 1 ? 's' : ''}`);
    if (pkg.allies)   benefitBits.push(`${pkg.allies} Ally${pkg.allies > 1 ? 'ies' : ''}`);
    if (pkg.equipment && pkg.equipment.length) benefitBits.push(pkg.equipment.join(', '));
    if (pkg.noble_title) benefitBits.push(pkg.noble_title);

    return `
      <button class="cp-card${isSel ? ' selected' : ''}${socBlock ? ' cp-card-locked' : ''}"
              data-cp-id="${escapeHTML(pkg.id)}"
              ${socBlock ? `title="Requires SOC ${minSoc}+ (you have ${character.characteristics.SOC})"` : ''}>
        <div class="cp-card-name">${escapeHTML(pkg.name)}</div>
        <div class="cp-card-stats">${escapeHTML(statMods)}</div>
        <div class="cp-card-desc">${escapeHTML(pkg.description || '')}</div>
        <div class="cp-card-benefits">${escapeHTML(benefitBits.join(' · '))}</div>
        ${socBlock ? '<div class="cp-card-lock">SOC ' + minSoc + '+ REQUIRED</div>' : ''}
      </button>`;
  }).join('');

  // Specialty pickers for the selected package
  let specSection = '';
  if (selId && CAREER_PACKAGES.packages && CAREER_PACKAGES.packages[selId]) {
    const pkg     = CAREER_PACKAGES.packages[selId];
    const anySkills = _cpAnySkills(pkg);
    if (anySkills.length) {
      const rows = anySkills.map(sk => {
        const key   = sk.key || sk.name;
        const val   = choices[key] || '';
        const isCasc = CASCADE_SKILLS[sk.name];
        let input;
        if (isCasc) {
          const chips = isCasc.map(spec =>
            `<button class="chip${val === spec ? ' active' : ''}"
                     data-cp-spec-key="${escapeHTML(key)}"
                     data-cp-spec-val="${escapeHTML(spec)}">${escapeHTML(spec)}</button>`
          ).join('');
          input = `<div class="pkg-spec-chips">${chips}</div>`;
        } else {
          input = `<input class="pkg-spec-input" type="text" placeholder="speciality…"
                          data-cp-spec-key="${escapeHTML(key)}"
                          value="${escapeHTML(val)}">`;
        }
        const label = sk.key ? `${sk.name} (${sk.key}) ${sk.level}` : `${sk.name} ${sk.level}`;
        return `<div class="pkg-spec-row">
          <span class="pkg-spec-label">${escapeHTML(label)}</span>
          ${input}
        </div>`;
      }).join('');
      specSection = `
        <div class="pkg-specialty-section">
          <div class="pkg-spec-heading">Choose specialities for this package's flexible skills:</div>
          ${rows}
        </div>`;
    }
  }

  // Enable NEXT only when all required specialties are filled
  let nextEnabled = false;
  if (selId && CAREER_PACKAGES.packages && CAREER_PACKAGES.packages[selId]) {
    const pkg = CAREER_PACKAGES.packages[selId];
    nextEnabled = _cpAnySkills(pkg).every(sk => {
      const key = sk.key || sk.name;
      return (choices[key] || '').trim().length > 0;
    });
    if (_cpAnySkills(pkg).length === 0) nextEnabled = true;
  }

  return `
    <div class="panel-header"><span class="led"></span><span>CAREER PACKAGE SELECTION</span></div>
    <div class="stage-content">
      <div class="phase-label">First Career · Age ${character.age}</div>
      <h2 class="phase-title">Choose a Career Package</h2>
      <p class="phase-subtitle">
        A career package replaces all normal career generation and provides a fixed set of skills and benefits.
        Only one package can be taken, and you cannot take any other careers afterwards.
        Your age will increase by 1–3 years (d3 roll on confirm).
      </p>
      <div class="cp-grid">${cards}</div>
      ${specSection}
      <div class="phase-actions" style="margin-top:16px;gap:8px">
        <button class="btn ghost" id="btn-cp-back">← BACK</button>
        <button class="btn primary" id="btn-cp-next" ${nextEnabled ? '' : 'disabled'}>
          NEXT: FINALISING OPTIONS →
        </button>
      </div>
    </div>`;
}

function renderCareerPackageFinalising() {
  const pkgId  = uiState.selectedCareerPackage;
  const pkg    = CAREER_PACKAGES.packages && CAREER_PACKAGES.packages[pkgId];
  if (!pkg) return '<div class="stage-content"><p>Error: no package selected.</p></div>';

  const fin    = CAREER_PACKAGES.finalising || {};
  const fc     = uiState.careerFinalising;
  const choices = uiState.careerPackageSkillChoices;

  // ── CAREER panel ────────────────────────────────────────────────────────
  const careerOptions = (fin.career || []).map(opt => {
    const isSel = fc.careerChoice === opt.id;
    let extra = '';
    if (isSel && opt.id === 'boost_one_to_4') {
      // Show dropdown of package skills at level 1+
      const eligible = (pkg.skills || []).filter(sk => sk.level >= 1);
      const skillOptions = eligible.map(sk => {
        const key  = sk.key || sk.name;
        const spec = sk.speciality || (sk.any ? choices[key] : null);
        const label = spec ? `${sk.name} (${spec})` : sk.name;
        const selVal = fc.careerSkill
          ? (fc.careerSkill.name === sk.name && (fc.careerSkill.speciality || '') === (spec || '') ? 'selected' : '')
          : '';
        return `<option value="${escapeHTML(sk.name)}|${escapeHTML(spec || '')}" ${selVal}>${escapeHTML(label)} ${sk.level}</option>`;
      }).join('');
      extra = `<select class="cp-fin-select" id="cp-boost1-select"><option value="">— pick skill —</option>${skillOptions}</select>`;
    }
    if (isSel && opt.id === 'boost_three_by_1') {
      const allSkills = (pkg.skills || []);
      const rows = [0, 1, 2].map(i => {
        const cur = fc.career3Skills[i];
        const skillOpts = allSkills.map(sk => {
          const key  = sk.key || sk.name;
          const spec = sk.speciality || (sk.any ? choices[key] : null);
          const label = spec ? `${sk.name} (${spec})` : sk.name;
          const selVal = cur && cur.name === sk.name && (cur.speciality || '') === (spec || '') ? 'selected' : '';
          return `<option value="${escapeHTML(sk.name)}|${escapeHTML(spec || '')}" ${selVal}>${escapeHTML(label)}</option>`;
        }).join('');
        return `<select class="cp-fin-select cp-boost3-select" data-idx="${i}">
          <option value="">— skill ${i + 1} —</option>${skillOpts}</select>`;
      }).join('');
      extra = `<div style="display:flex;flex-direction:column;gap:4px;margin-top:4px">${rows}</div>`;
    }
    return `
      <label class="cp-fin-option${isSel ? ' selected' : ''}">
        <input type="radio" name="cp-career-choice" value="${escapeHTML(opt.id)}" ${isSel ? 'checked' : ''}>
        <div class="cp-fin-label">${escapeHTML(opt.label)}</div>
        <div class="cp-fin-desc">${escapeHTML(opt.description)}</div>
        ${extra}
      </label>`;
  }).join('');

  // ── TRAVELLER SKILLS panel ───────────────────────────────────────────────
  const tsPairs = (fin.traveller_skills || []).map(pair => {
    const isSel = fc.travellerPairId === pair.id;
    let specInputs = '';
    if (isSel) {
      const anyS = (pair.skills || []).filter(s => s.any);
      if (anyS.length) {
        specInputs = anyS.map(sk => {
          const key   = sk.key || sk.name;
          const val   = fc.travellerSpecialties[key] || '';
          const isCasc = CASCADE_SKILLS[sk.name];
          let inp;
          if (isCasc) {
            const chips = isCasc.map(spec =>
              `<button class="chip${val === spec ? ' active' : ''}"
                       data-ts-spec-key="${escapeHTML(key)}"
                       data-ts-spec-val="${escapeHTML(spec)}">${escapeHTML(spec)}</button>`
            ).join('');
            inp = `<div class="pkg-spec-chips">${chips}</div>`;
          } else {
            inp = `<input class="pkg-spec-input" type="text" placeholder="${escapeHTML(sk.name)} speciality…"
                          data-ts-spec-key="${escapeHTML(key)}"
                          value="${escapeHTML(val)}">`;
          }
          return `<div class="pkg-spec-row">
            <span class="pkg-spec-label">${escapeHTML(sk.name)} specialty:</span>
            ${inp}
          </div>`;
        }).join('');
        specInputs = `<div class="pkg-specialty-section" style="margin-top:4px">${specInputs}</div>`;
      }
    }
    return `
      <label class="cp-fin-option${isSel ? ' selected' : ''}">
        <input type="radio" name="cp-ts-choice" value="${pair.id}" ${isSel ? 'checked' : ''}>
        <div class="cp-fin-label">${escapeHTML(pair.label)}</div>
        ${specInputs}
      </label>`;
  }).join('');

  // ── BENEFITS panel ───────────────────────────────────────────────────────
  const benefitRows = (fin.benefits || []).map(b => {
    const isSel = fc.benefitId === b.id;
    return `
      <label class="cp-fin-option${isSel ? ' selected' : ''}">
        <input type="radio" name="cp-benefit-choice" value="${b.id}" ${isSel ? 'checked' : ''}>
        <div class="cp-fin-label">${escapeHTML(b.label)}</div>
      </label>`;
  }).join('');

  // Confirm enabled?
  const tsOk = fc.travellerPairId !== null && (() => {
    const pair = (fin.traveller_skills || []).find(p => p.id === fc.travellerPairId);
    if (!pair) return false;
    return (pair.skills || []).filter(s => s.any).every(sk => {
      const key = sk.key || sk.name;
      return (fc.travellerSpecialties[key] || '').trim().length > 0;
    });
  })();
  const careerOk = fc.careerChoice !== null && (() => {
    if (fc.careerChoice === 'boost_one_to_4') return fc.careerSkill !== null;
    if (fc.careerChoice === 'boost_three_by_1') return fc.career3Skills.filter(Boolean).length === 3;
    return true;
  })();
  const confirmEnabled = careerOk && tsOk && fc.benefitId !== null;

  return `
    <div class="panel-header"><span class="led"></span><span>CAREER PACKAGE — FINALISING</span></div>
    <div class="stage-content">
      <div class="phase-label">${escapeHTML(pkg.name)} · Age ${character.age}</div>
      <h2 class="phase-title">Finalising the Traveller</h2>
      <p class="phase-subtitle">
        Choose one option from each of the three categories below to tailor your Traveller.
      </p>

      <div class="cp-fin-section">
        <div class="cp-fin-heading">CAREER</div>
        <div class="cp-fin-desc" style="margin-bottom:8px">
          <em>One option from career improvements:</em>
        </div>
        ${careerOptions}
      </div>

      <div class="cp-fin-section">
        <div class="cp-fin-heading">TRAVELLER SKILLS</div>
        <div class="cp-fin-desc" style="margin-bottom:8px">
          <em>Choose one skill pair — both skills granted at level 1:</em>
        </div>
        <div class="cp-ts-grid">${tsPairs}</div>
      </div>

      <div class="cp-fin-section">
        <div class="cp-fin-heading">BENEFITS</div>
        <div class="cp-fin-desc" style="margin-bottom:8px">
          <em>Choose one muster-out benefit:</em>
        </div>
        <div class="cp-ts-grid">${benefitRows}</div>
      </div>

      <div class="phase-actions" style="margin-top:16px;gap:8px">
        <button class="btn ghost" id="btn-cp-fin-back">← BACK</button>
        <button class="btn primary" id="btn-cp-confirm" ${confirmEnabled ? '' : 'disabled'}>
          CONFIRM CAREER PACKAGE →
        </button>
      </div>
    </div>`;
}

function wireCareerPackagePicker() {
  // Package card selection
  document.querySelectorAll('[data-cp-id]').forEach(card => {
    card.addEventListener('click', () => {
      const id  = card.dataset.cpId;
      const pkg = CAREER_PACKAGES.packages && CAREER_PACKAGES.packages[id];
      const minSoc = pkg && pkg.min_soc;
      if (minSoc && character.characteristics.SOC < minSoc) return; // blocked
      if (uiState.selectedCareerPackage === id) return;
      uiState.selectedCareerPackage     = id;
      uiState.careerPackageSkillChoices = {};
      renderAll();
    });
  });

  // Specialty chip clicks
  document.querySelectorAll('[data-cp-spec-key]').forEach(chip => {
    if (chip.tagName === 'BUTTON') {
      chip.addEventListener('click', e => {
        e.stopPropagation();
        const key = chip.dataset.cpSpecKey;
        const val = chip.dataset.cpSpecVal;
        uiState.careerPackageSkillChoices[key] = val;
        renderAll();
      });
    }
  });

  // Specialty text inputs
  document.querySelectorAll('input[data-cp-spec-key]').forEach(inp => {
    inp.addEventListener('input', () => {
      uiState.careerPackageSkillChoices[inp.dataset.cpSpecKey] = inp.value;
      // Re-enable NEXT button without full re-render
      const btn = document.getElementById('btn-cp-next');
      if (btn) {
        const pkgId = uiState.selectedCareerPackage;
        const pkg   = CAREER_PACKAGES.packages && CAREER_PACKAGES.packages[pkgId];
        if (pkg) {
          const ok = _cpAnySkills(pkg).every(sk => {
            const k = sk.key || sk.name;
            return (uiState.careerPackageSkillChoices[k] || '').trim().length > 0;
          });
          btn.disabled = !ok;
        }
      }
    });
  });

  // BACK button
  const btnBack = document.getElementById('btn-cp-back');
  if (btnBack) {
    btnBack.addEventListener('click', () => {
      uiState.careerPackageMode = false;
      uiState.selectedCareerPackage = null;
      renderAll();
    });
  }

  // NEXT button → go to finalising
  const btnNext = document.getElementById('btn-cp-next');
  if (btnNext) {
    btnNext.addEventListener('click', () => {
      uiState.careerPackagePhase = 'finalising';
      uiState.careerFinalising = {
        careerChoice: null, careerSkill: null, career3Skills: [],
        travellerPairId: null, travellerSpecialties: {}, benefitId: null,
      };
      renderAll();
    });
  }
}

function wireCareerPackageFinalising() {
  // Career choice radio buttons
  document.querySelectorAll('input[name="cp-career-choice"]').forEach(radio => {
    radio.addEventListener('change', () => {
      uiState.careerFinalising.careerChoice  = radio.value;
      uiState.careerFinalising.careerSkill   = null;
      uiState.careerFinalising.career3Skills = [];
      renderAll();
    });
  });

  // boost_one_to_4 skill dropdown
  const boost1sel = document.getElementById('cp-boost1-select');
  if (boost1sel) {
    boost1sel.addEventListener('change', () => {
      const [name, spec] = boost1sel.value.split('|');
      uiState.careerFinalising.careerSkill = { name, speciality: spec || null };
      renderAll();
    });
  }

  // boost_three_by_1 skill dropdowns
  document.querySelectorAll('.cp-boost3-select').forEach(sel => {
    sel.addEventListener('change', () => {
      const idx  = parseInt(sel.dataset.idx);
      const [name, spec] = sel.value.split('|');
      const arr  = [...(uiState.careerFinalising.career3Skills || [])];
      arr[idx]   = { name, speciality: spec || null };
      uiState.careerFinalising.career3Skills = arr;
      // refresh CONFIRM button state
      const btn = document.getElementById('btn-cp-confirm');
      if (btn) {
        const fc = uiState.careerFinalising;
        const fin = CAREER_PACKAGES.finalising || {};
        const tsOk = fc.travellerPairId !== null && (() => {
          const pair = (fin.traveller_skills || []).find(p => p.id === fc.travellerPairId);
          if (!pair) return false;
          return (pair.skills || []).filter(s => s.any).every(sk => {
            const k = sk.key || sk.name;
            return (fc.travellerSpecialties[k] || '').trim().length > 0;
          });
        })();
        const careerOk = fc.careerChoice !== null && (() => {
          if (fc.careerChoice === 'boost_one_to_4') return fc.careerSkill !== null;
          if (fc.careerChoice === 'boost_three_by_1') return arr.filter(Boolean).length === 3 && arr.every(x => x && x.name);
          return true;
        })();
        btn.disabled = !(careerOk && tsOk && fc.benefitId !== null);
      }
    });
  });

  // Traveller skills radio
  document.querySelectorAll('input[name="cp-ts-choice"]').forEach(radio => {
    radio.addEventListener('change', () => {
      uiState.careerFinalising.travellerPairId    = parseInt(radio.value);
      uiState.careerFinalising.travellerSpecialties = {};
      renderAll();
    });
  });

  // Traveller skills specialty chips
  document.querySelectorAll('[data-ts-spec-key]').forEach(el => {
    if (el.tagName === 'BUTTON') {
      el.addEventListener('click', e => {
        e.stopPropagation();
        uiState.careerFinalising.travellerSpecialties[el.dataset.tsSpecKey] = el.dataset.tsSpecVal;
        renderAll();
      });
    } else if (el.tagName === 'INPUT') {
      el.addEventListener('input', () => {
        uiState.careerFinalising.travellerSpecialties[el.dataset.tsSpecKey] = el.value;
      });
    }
  });

  // Benefit radio
  document.querySelectorAll('input[name="cp-benefit-choice"]').forEach(radio => {
    radio.addEventListener('change', () => {
      uiState.careerFinalising.benefitId = parseInt(radio.value);
      renderAll();
    });
  });

  // BACK button → back to package picker
  const btnBack = document.getElementById('btn-cp-fin-back');
  if (btnBack) {
    btnBack.addEventListener('click', () => {
      uiState.careerPackagePhase = 'picker';
      renderAll();
    });
  }

  // CONFIRM button → POST to backend
  const btnConfirm = document.getElementById('btn-cp-confirm');
  if (btnConfirm) {
    btnConfirm.addEventListener('click', async () => {
      btnConfirm.disabled = true;
      btnConfirm.textContent = 'APPLYING…';
      const fc = uiState.careerFinalising;
      try {
        const payload = {
          package_id:             uiState.selectedCareerPackage,
          skill_choices:          uiState.careerPackageSkillChoices,
          career_choice:          fc.careerChoice,
          career_skill:           fc.careerSkill ? fc.careerSkill.name : null,
          career_skill_speciality: fc.careerSkill ? (fc.careerSkill.speciality || null) : null,
          career_3skills:         (fc.career3Skills || []).filter(Boolean).map(x => ({
            name: x.name, speciality: x.speciality || null
          })),
          traveller_pair_id:      fc.travellerPairId,
          traveller_specialties:  fc.travellerSpecialties || {},
          benefit_id:             fc.benefitId,
        };
        const response = await apiCall('/api/character/career-package', payload);
        await applyResponse(response);
        // Reset career package UI state
        uiState.careerPackageMode     = false;
        uiState.careerPackagePhase    = 'picker';
        uiState.selectedCareerPackage = null;
        uiState.careerPackageSkillChoices = {};
        uiState.careerFinalising = {
          careerChoice: null, careerSkill: null, career3Skills: [],
          travellerPairId: null, travellerSpecialties: {}, benefitId: null,
        };
        renderAll();
      } catch (e) {
        btnConfirm.disabled  = false;
        btnConfirm.textContent = 'CONFIRM CAREER PACKAGE →';
        alert(e.message || 'Failed to apply career package.');
      }
    });
  }
}

function wireCareerPhase() {
  if (uiState.careerPackageMode) {
    if (uiState.careerPackagePhase === 'finalising') {
      wireCareerPackageFinalising();
    } else {
      wireCareerPackagePicker();
    }
    return;
  }

  // "Use career package" button on the career picker
  const btnCPkg = document.querySelector('.btn-use-career-package');
  if (btnCPkg) {
    btnCPkg.addEventListener('click', () => {
      uiState.careerPackageMode  = true;
      uiState.careerPackagePhase = 'picker';
      uiState.selectedCareerPackage = null;
      uiState.careerPackageSkillChoices = {};
      uiState.careerFinalising = {
        careerChoice: null, careerSkill: null, career3Skills: [],
        travellerPairId: null, travellerSpecialties: {}, benefitId: null,
      };
      renderAll();
    });
  }

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
      uiState.lastRoll = null;             // clear any stale roll from the previous term
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

  // Passing Documents: purchase
  const btnPassingDocs = document.getElementById('btn-passing-docs');
  if (btnPassingDocs) {
    btnPassingDocs.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/solomani-documents', {});
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
          const resolved = `+1 ${pending.skillName} (${spec}) (level 1)`;
          uiState.lastRoll.applied = resolved;
          // Advancement bonus-skill flow stores the gain under a different field
          // and mirrors it onto lastAdvanceRoll — keep both in sync so the
          // resolved specialty shows instead of "… speciality choice pending".
          if (uiState.lastRoll.type === 'advance') {
            uiState.lastRoll.advancementSkillGained = resolved;
            if (uiState.lastAdvanceRoll) uiState.lastAdvanceRoll.advancementSkillGained = resolved;
          }
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

  // Storm Knight Heroism buttons — set DM before survival roll
  document.querySelectorAll('.btn-heroism-choice').forEach(btn => {
    btn.addEventListener('click', async () => {
      const dm = parseInt(btn.dataset.dm, 10);
      const response = await apiCall('/api/character/storm-knight-heroism', { dm });
      await applyResponse(response);
      renderAll();
    });
  });

  const btnSurvive = document.getElementById('btn-survive');
  if (btnSurvive) {
    btnSurvive.addEventListener('click', async () => {
      const response = await apiCall('/api/character/survive');
      await applyResponse(response);
      uiState.lastRoll = {
        type: 'survive',
        data: response.roll,
        outcome: response.survived ? 'pass' : 'fail',
        mishapNoEject: response.mishap_no_eject || false,
        parallel_event: response.parallel_event || null,
        anagathics_second_roll: response.anagathics_second_roll || null,
        passing_exposed: response.passing_exposed || false,
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
      // Carry mishapNoEject into the mishap subPhase so the mishap roll result
      // knows the career doesn't eject on mishap (e.g. Bounty Hunter).
      uiState.pendingMishapNoEject = uiState.lastRoll?.mishapNoEject || false;
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
        eventEffects: response.event_effects || [],
        pendingEventChoice: response.pending_event_choice || null,
        disasterMishap: response.disaster_mishap || null,
        // When the event has a pending_choice handler, all associate grants are
        // applied by the choice resolver — suppress text-parsed associate ops to
        // avoid duplicate picker UIs and duplicate associates.
        // Also suppress when:
        //   • event_effects already contain an auto-applied contact (e.g. event 10)
        //   • a life event pending choice is set (the life event UI owns the picker)
        // Any structured pending_event_choice (skill_check, pending_choice,
        // skill_choice, …) owns the event's associates via its on_pass/on_fail
        // or top-level effects, so the text-parsed associate picker must stand
        // down — otherwise e.g. bounty_hunter[9] "gain an Enemy" is applied both
        // by the skill_check's on_fail and by the manual "+ Add Enemy" op.
        suppressAssocOps: !!(
          response.pending_event_choice ||
          (response.event_effects || []).some(e => /^gained contact:/i.test(e)) ||
          (response.event_effects || []).some(e => /converted to/i.test(e)) ||
          !!(response.character?.pending_life_event_choice)
        ),
      };

      // Auto-add unambiguous single Ally grants without requiring the picker.
      // "Allies should always be added to the associates" — only skip if
      // quantity ops are present (D3 Allies etc.) since those need a die roll
      // to determine count.
      const rawAssocOpsForEvent = parseEventAssociateOps(response.event || '');
      const hasQuantityOps = rawAssocOpsForEvent.some(op => op.type === 'quantity');
      // Skip auto-add when structured effects own the associates (see
      // suppressAssocOps above) — otherwise a structured ally grant would be
      // duplicated by this text-parsed auto-add.
      if (!hasQuantityOps && !uiState.lastRoll.suppressAssocOps) {
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
            // Event says character is not ejected (e.g. Merchant[2])
            noEject: /not ejected|career continues/i.test(uiState.lastRoll?.eventText || ''),
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

  // Solomani D66 contact generator buttons
  document.querySelectorAll('[data-solomani-gen]').forEach(btn => {
    btn.addEventListener('click', () => {
      const opIdx = parseInt(btn.getAttribute('data-solomani-gen'), 10);
      const descEl = document.querySelector(`[data-assoc-desc="${opIdx}"]`);
      if (!descEl) return;
      const d1 = Math.ceil(Math.random() * 6);
      const d2 = Math.ceil(Math.random() * 6);
      const personage = _SOL_CONTACTS[d1 * 10 + d2] || 'Unknown Personage';
      const name = generateSpeciesName(character.species_id || 'solomani_human');
      descEl.value = `${personage} — ${name}`;
      descEl.dispatchEvent(new Event('input'));
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
      const noEject = uiState.pendingMishapNoEject || false;
      uiState.pendingMishapNoEject = false;
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
        mishapNoEject: noEject,
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

  // Bounty Hunter (and similar): mishap does not eject from career — continue as normal
  const btnPostMishapContinue = document.getElementById('btn-post-mishap-continue');
  if (btnPostMishapContinue) {
    btnPostMishapContinue.addEventListener('click', () => {
      uiState.lastRoll = null;
      uiState.subPhase = 'advance';
      renderStage();
    });
  }

  // Helper: call career-event-choice and refresh state
  async function resolveEventChoice(choiceData) {
    const response = await apiCall('/api/character/career-event-choice', { choice_data: choiceData });
    await applyResponse(response);
    if (uiState.lastRoll && uiState.lastRoll.type === 'event') {
      uiState.lastRoll.pendingEventChoice = response.pending_event_choice || null;
      if (response.event_effects) {
        uiState.lastRoll.eventEffects = (uiState.lastRoll.eventEffects || []).concat(response.event_effects);
      }
      if (response.disaster_mishap) {
        uiState.lastRoll.disasterMishap = response.disaster_mishap;
      }
      if (response.skill_check) {
        uiState.lastRoll.skillCheckResult = response.skill_check;
      }
      if (response.auto_applied && response.auto_applied.length) {
        uiState.lastRoll.eventEffects = (uiState.lastRoll.eventEffects || []).concat(response.auto_applied);
      }
    }
    renderAll();
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

  // Skill loss choice buttons — pick a skill to lose one level
  document.querySelectorAll('[id^="btn-mishap-skillloss-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const raw = btn.id.replace('btn-mishap-skillloss-', '');
      if (raw === 'none') {
        resolveMishapChoice({ skill: '' });
      } else {
        resolveMishapChoice({ skill: raw });
      }
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

  // Party mishap 5 — optional Ally gain (fellow sufferer)
  const btnParty5AllyAccept = document.getElementById('btn-mishap-party5ally-accept');
  if (btnParty5AllyAccept) btnParty5AllyAccept.addEventListener('click', () => resolveMishapChoice({ option_id: 'accept' }));
  const btnParty5AllyDecline = document.getElementById('btn-mishap-party5ally-decline');
  if (btnParty5AllyDecline) btnParty5AllyDecline.addEventListener('click', () => resolveMishapChoice({ option_id: 'decline' }));

  // SolSec interrogation choice
  const btnIntSubmit = document.getElementById('btn-mishap-interrogation-submit');
  if (btnIntSubmit) btnIntSubmit.addEventListener('click', () => resolveMishapChoice({ option_id: 'submit' }));
  const btnIntRefuse = document.getElementById('btn-mishap-interrogation-refuse');
  if (btnIntRefuse) btnIntRefuse.addEventListener('click', () => resolveMishapChoice({ option_id: 'refuse' }));

  // Aslan brave/refuse choice (military mishap 5)
  const btnBraveFight = document.getElementById('btn-mishap-brave-fight');
  if (btnBraveFight) btnBraveFight.addEventListener('click', () => resolveMishapChoice({ option_id: 'fight' }));
  const btnBraveRefuse = document.getElementById('btn-mishap-brave-refuse');
  if (btnBraveRefuse) btnBraveRefuse.addEventListener('click', () => resolveMishapChoice({ option_id: 'refuse' }));

  // Aslan management accused choice (management mishap 2)
  const btnMgmtGuilty = document.getElementById('btn-mishap-mgmt-guilty');
  if (btnMgmtGuilty) btnMgmtGuilty.addEventListener('click', () => resolveMishapChoice({ option_id: 'guilty' }));
  const btnMgmtInnocent = document.getElementById('btn-mishap-mgmt-innocent');
  if (btnMgmtInnocent) btnMgmtInnocent.addEventListener('click', () => resolveMishapChoice({ option_id: 'innocent' }));

  // Aslan scientist leave choice (scientist mishap 6)
  const btnScientistLeave = document.getElementById('btn-mishap-scientist-leave');
  if (btnScientistLeave) btnScientistLeave.addEventListener('click', () => resolveMishapChoice({ option_id: 'leave' }));
  const btnScientistAccept = document.getElementById('btn-mishap-scientist-accept');
  if (btnScientistAccept) btnScientistAccept.addEventListener('click', () => resolveMishapChoice({ option_id: 'accept' }));

  // GE forced career choice (fleet mishap 4, warrior mishap 4)
  const btnGELandless = document.getElementById('btn-mishap-ge-landless');
  if (btnGELandless) btnGELandless.addEventListener('click', () => resolveMishapChoice({ option_id: 'landless_one' }));
  const btnGEOutlaw = document.getElementById('btn-mishap-ge-outlaw');
  if (btnGEOutlaw) btnGEOutlaw.addEventListener('click', () => resolveMishapChoice({ option_id: 'outlaw' }));

  // GE Hierate capture choice (fleet officer mishap 5, warrior officer mishap 5)
  const btnGEReturn = document.getElementById('btn-mishap-ge-return');
  if (btnGEReturn) btnGEReturn.addEventListener('click', () => resolveMishapChoice({ option_id: 'return' }));
  const btnGEStay = document.getElementById('btn-mishap-ge-stay');
  if (btnGEStay) btnGEStay.addEventListener('click', () => resolveMishapChoice({ option_id: 'stay' }));

  // GE Slave revolt choice (slave mishap 4)
  const btnSlaveReport = document.getElementById('btn-mishap-slave-report');
  if (btnSlaveReport) btnSlaveReport.addEventListener('click', () => resolveMishapChoice({ option_id: 'report' }));
  const btnSlaveAllow = document.getElementById('btn-mishap-slave-allow');
  if (btnSlaveAllow) btnSlaveAllow.addEventListener('click', () => resolveMishapChoice({ option_id: 'allow' }));

  // GE Landless One lose-associate-or-forfeit dynamic buttons
  document.querySelectorAll('[id^="btn-mishap-lose-assoc-"]').forEach(btn => {
    btn.addEventListener('click', () => resolveMishapChoice({ option_id: btn.dataset.optionId }));
  });

  // Vargr army — join ring or testify
  const btnVargrArmyJoin = document.getElementById('btn-mishap-vargrarmy-join');
  if (btnVargrArmyJoin) btnVargrArmyJoin.addEventListener('click', () => resolveMishapChoice({ option_id: 'join' }));
  const btnVargrArmyTestify = document.getElementById('btn-mishap-vargrarmy-testify');
  if (btnVargrArmyTestify) btnVargrArmyTestify.addEventListener('click', () => resolveMishapChoice({ option_id: 'testify' }));

  // Vargr citizen — aid investigation or refuse
  const btnVargrCitiAid = document.getElementById('btn-mishap-vargrcitiaid');
  if (btnVargrCitiAid) btnVargrCitiAid.addEventListener('click', () => resolveMishapChoice({ option_id: 'aid' }));
  const btnVargrCitiRefuse = document.getElementById('btn-mishap-vargrcitirefuse');
  if (btnVargrCitiRefuse) btnVargrCitiRefuse.addEventListener('click', () => resolveMishapChoice({ option_id: 'refuse' }));

  // Vargr corsair betrayal — dynamic options (pick contact/ally or auto-enemy)
  document.querySelectorAll('[id^="btn-mishap-vargrbetray-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const optId = btn.dataset.optionId;
      const assocIdx = btn.dataset.assocIdx;
      if (optId === 'auto_enemy') {
        resolveMishapChoice({ option_id: 'auto_enemy' });
      } else {
        resolveMishapChoice({ option_id: optId, associate_index: parseInt(assocIdx, 10) });
      }
    });
  });

  // Vargr law enforcement — accept deal or refuse
  const btnVargrLawAccept = document.getElementById('btn-mishap-vargrlaw-accept');
  if (btnVargrLawAccept) btnVargrLawAccept.addEventListener('click', () => resolveMishapChoice({ option_id: 'accept' }));
  const btnVargrLawRefuse = document.getElementById('btn-mishap-vargrlaw-refuse');
  if (btnVargrLawRefuse) btnVargrLawRefuse.addEventListener('click', () => resolveMishapChoice({ option_id: 'refuse' }));

  // Vargr scientist — stay quietly or roll SOC 8+
  const btnVargrSciStay = document.getElementById('btn-mishap-vargrsci-stay');
  if (btnVargrSciStay) btnVargrSciStay.addEventListener('click', () => resolveMishapChoice({ option_id: 'stay' }));
  const btnVargrSciRoll = document.getElementById('btn-mishap-vargrsci-roll');
  if (btnVargrSciRoll) btnVargrSciRoll.addEventListener('click', () => resolveMishapChoice({ option_id: 'roll_soc' }));

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

  // Generic pending_choice option buttons (fallback for all choices with options array)
  document.querySelectorAll('.generic-pending-opt').forEach(btn => {
    btn.addEventListener('click', () => {
      const optId = btn.dataset.optionId;
      resolveMishapChoice({ option_id: optId });
    });
  });

  // Skill check buttons
  document.querySelectorAll('[id^="btn-mishap-skillcheck-"]').forEach(btn => {
    btn.addEventListener('click', () => {
      const skillName = btn.getAttribute('data-skill');
      resolveMishapChoice({ skill_name: skillName });
    });
  });

  // ---- Career-phase inline life event choice buttons (btn-career-life-choice-*) ----
  // These fire when event 7 produces a pending_life_event_choice during a career term.
  document.querySelectorAll('[id^="btn-career-life-choice-"]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const choice = btn.id.replace('btn-career-life-choice-', '');
      try {
        const response = await apiCall('/api/character/life-event-choice', { choice });
        await applyResponse(response);
        renderAll();
      } catch (e) { alert(e.message); }
    });
  });

  // ---- Event choice buttons (pending_career_event_choice) ----

  // skill_choice: pick one skill from a list
  document.querySelectorAll('.event-choice-skill').forEach(btn => {
    btn.addEventListener('click', () => {
      const skill = btn.getAttribute('data-event-choice-skill');
      resolveEventChoice({ skill }).then(() => {
        if (uiState.lastRoll && !uiState.lastRoll.pendingEventChoice) uiState.lastRoll.eventChoiceResolved = true;
        renderAll();
      });
    });
  });

  // free_skill_choice: type a skill name
  const btnEventFreeskillConfirm = document.getElementById('btn-event-freeskill-confirm');
  if (btnEventFreeskillConfirm) {
    btnEventFreeskillConfirm.addEventListener('click', async () => {
      const input = document.getElementById('input-event-freeskill');
      const skill = input ? input.value.trim() : '';
      if (!skill) { alert('Enter a skill name.'); return; }
      await resolveEventChoice({ skill });
      if (uiState.lastRoll && !uiState.lastRoll.pendingEventChoice) uiState.lastRoll.eventChoiceResolved = true;
      renderAll();
    });
  }

  // skill_check: pick skill and auto-roll
  document.querySelectorAll('.event-choice-skillcheck').forEach(btn => {
    btn.addEventListener('click', async () => {
      const skillName = btn.getAttribute('data-skill-name');
      await resolveEventChoice({ skill_name: skillName });
      if (uiState.lastRoll && !uiState.lastRoll.pendingEventChoice) uiState.lastRoll.eventChoiceResolved = true;
      renderAll();
    });
  });

  // pending_choice: pick an option by id
  document.querySelectorAll('.event-choice-pending').forEach(btn => {
    btn.addEventListener('click', async () => {
      const optionId = btn.getAttribute('data-event-choice-option');
      await resolveEventChoice({ option_id: optionId });
      // Only mark resolved when there is no chained follow-up pending
      if (uiState.lastRoll && !uiState.lastRoll.pendingEventChoice) {
        uiState.lastRoll.eventChoiceResolved = true;
      }
      renderAll();
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
          rankBonus: response.rank_bonus || null,
          forcedFromCareer: response.forced_from_career || false,
          knightCommanderByRank: response.knight_commander_by_rank || false,
          knightGrandCross: response.knight_grand_cross || false,
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
        // A bare cascade skill (e.g. Melee, Gun Combat) needs a specialty pick.
        // Mirror the training-phase flow: stash pendingCareerSpecialty so the
        // advancement result view renders the specialty picker (and gates the
        // term-decision buttons) instead of silently leaving it "pending".
        const advBareSkill = (response.result || '').trim();
        uiState.pendingCareerSpecialty = CASCADE_SKILLS[advBareSkill]
          ? { skillName: advBareSkill, level: 1, tableKey, rollData: response.roll,
              result: response.result, applied: response.applied }
          : null;
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
      // Intercept for anagathics before starting the next term — but only when the
      // player hasn't opted out. Mirrors the guard in renderCareerPhase() so that
      // anagathics_interest:'no' characters never get stuck in the intercept.
      const anaInterest = character.anagathics_interest;
      if (!uiState.anagathicsPhaseDone && anaInterest !== 'no') {
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
    } else if (nextAction.type === 'career_select') {
      // End term without leaving — drop back into career picker (e.g. to try a semi-career)
      uiState.lastRoll = null;
      uiState.subPhase = null;
      uiState.selectedCareer = null;
      uiState.selectedAssignment = null;
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

  // Semi-career try-out buttons (e.g. "TRY OUT FOR IMPERIAL GUARD")
  // End the current term (non-leaving) then drop into the career picker,
  // where the semi-career card will be visible.
  document.querySelectorAll('.btn-try-semi-career').forEach(btn => {
    btn.addEventListener('click', async () => {
      await endTermWithAgingIntercept(false, 'voluntary', { type: 'career_select' });
    });
  });

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
          uiState.lastRoll = { ...uiState.lastRoll, injuryPending: false, treatmentPending: true };
          renderAll();
          return;
        }
        uiState.lastRoll = { ...uiState.lastRoll, injuryPending: false };
        renderAll();
      } catch (e) { alert(e.message); }
    });
    // Same handler for injury from an event-triggered non-ejecting mishap
    const btnEv = document.getElementById(`btn-event-mishap-injury-stat-${stat}`);
    if (btnEv) btnEv.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/injury-choice', { chosen_stat: stat });
        await applyResponse(response);
        if (response.treatment_choice_pending) {
          uiState.lastRoll = { ...uiState.lastRoll, treatmentPending: true };
          renderAll();
          return;
        }
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

// The career-loop sub-phase lives only in uiState, never in the saved character,
// so a page reload or imported save resumes with subPhase === null. Defaulting
// to the training step would drop the player back at Basic Training mid-term —
// stranding an unresolved Life Event / pending choice, and re-rolling
// survival+event if they continued. Infer the correct resume step from the term
// and any pending interactive choices, reconstructing the minimal lastRoll the
// event view needs so its picker (life event / structured choice) can render.
function inferResumeSubPhase(term) {
  const resumeEventRoll = () => {
    if (uiState.lastRoll && uiState.lastRoll.type === 'event') return;
    uiState.lastRoll = {
      type: 'event',
      data: null,
      eventText: (term.events && term.events.length) ? term.events[term.events.length - 1] : '',
      dmGrants: [], statBonuses: [], eventEffects: [], autoPromotion: null,
      associateOpsDone: [], suppressAssocOps: true,
      pendingEventChoice: character.pending_career_event_choice || null,
      disasterMishap: null, eventChoiceResolved: false,
    };
  };
  // 1. Unresolved interactive choices own the screen.
  if (character.pending_career_mishap_choice) return 'mishap';
  if (character.pending_life_event_choice || character.pending_career_event_choice) {
    resumeEventRoll();
    return 'event';
  }
  // 2. Advancement already rolled → term-end decision screen.
  if (term.advanced !== null && term.advanced !== undefined) return 'decide';
  // 3. Failed survival, mishap not yet resolved → mishap step.
  if (term.survived === false) return 'mishap';
  // 4. Survived: event already rolled → advancement; otherwise go roll the event.
  if (term.survived === true) return (term.events && term.events.length) ? 'advance' : 'event';
  // 5. Fresh term, not yet survived — normal training/survival entry.
  return 'train';
}

function renderActiveTerm() {
  const term = character.current_term;
  const career = CAREERS.find(c => c.id === term.career_id);
  const assignment = career.assignments[term.assignment_id];

  const banner = `
    <div class="term-banner">
      <span class="term-part"><strong>${esc(career.name)}</strong> · ${esc(assignment.name)}</span>
      <span class="term-part">TERM <strong>${term.overall_term_number}</strong> · AGE <strong>${character.age}</strong></span>
      <span class="term-part">RANK <strong>${term.rank}</strong>${term.rank_title ? ` — ${esc(term.rank_title)}` : ''}</span>
    </div>
  `;

  // Resume support: when the sub-phase was lost (reload / import), infer it from
  // term state instead of defaulting to Basic Training.
  if (uiState.subPhase === null) {
    uiState.subPhase = inferResumeSubPhase(term);
  }

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
        <div class="phase-label">${esc(career.name)}</div>
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
        <div class="phase-label">${esc(career.name)}</div>
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
        <div class="phase-label">${esc(career.name)}</div>
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
            <div class="card-title" style="font-size:12px">${esc(c.name)}</div>
          </button>
        `).join('')}
      </div>
      ${uiState.selectedCoverCareer ? `
        <p style="font-size:11px;color:var(--accent);margin-top:8px">
          ✓ Cover: <strong>${esc(CAREERS.find(c=>c.id===uiState.selectedCoverCareer)?.name)}</strong>
          — survival and advancement use this career's stats (DM-1 / DM+1).
        </p>` : `
        <p style="font-size:11px;color:var(--text-dim);margin-top:8px">Select a cover career above to continue.</p>
      `}
    </div>
  ` : '';

  const readyToStart = uiState.selectedAssignment &&
    (!isSecretAgentSelected || uiState.selectedCoverCareer);

  const charGender = character.gender || null;
  const cards = Object.entries(career.assignments).map(([id, a]) => {
    // Aslan gender-restricted assignments: hide disallowed ones entirely
    if (a.allowed_genders && a.allowed_genders.length > 0 && charGender) {
      if (!a.allowed_genders.includes(charGender)) return '';
    }
    return `
    <button class="card ${uiState.selectedAssignment === id ? 'selected' : ''}" data-assignment="${id}">
      <div class="card-title">${esc(a.name)}</div>
      <div class="card-meta">SURV ${a.survival.characteristic} ${a.survival.target}+ · ADV ${a.advancement.characteristic} ${a.advancement.target}+</div>
      <div class="card-desc">${esc(a.description)}</div>
    </button>`;
  }).join('');

  // ---- Solomani parallel service panels ----
  const isSolomani = (character.society_id === 'solomani_confederation');
  // Home Forces Reserves is a PARALLEL civilian reserve — full-time military careers are ineligible.
  const isBarredFromHF = (career.id === 'drifter')
    || (career.id === 'rogue' && uiState.selectedAssignment === 'pirate')
    || (career.id === 'solsec')
    || (career.id === 'solomani_marine')
    || (career.id === 'confederation_army')
    || (career.id === 'confederation_navy');
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

  // Passing Documents — available to solomani_mixed characters only.
  // Once purchased they can never be re-purchased (solomani_passing stays true or
  // is revoked permanently on exposure).
  const showPassingDocs = isSolomani && character.species_id === 'solomani_mixed';
  const passingDocColor = character.solomani_passing ? 'var(--accent)' : 'var(--text-dim)';
  const passingDocsHTML = showPassingDocs ? `
    <div style="margin-top:10px;padding:12px 14px;border:1px solid var(--border);border-radius:6px">
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <div style="flex:1;min-width:200px">
          <div style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">
            SOLOMANI PASSING DOCUMENTS${character.solomani_passing ? ' · ACTIVE' : ''}
          </div>
          <div style="font-size:12px;color:${passingDocColor};margin-top:3px">
            ${character.solomani_passing
              ? 'Falsified genetic records held — treated as Racial Solomani for qualification (Party Patronage DM; no Mixed Heritage penalty). Exposed on a natural 2 in military/Party careers: SOC halved, status revoked.'
              : 'Falsified genetic records remove the Mixed Heritage qualification penalty and grant Party Patronage DM. Cost: 30,000 Cr (debt). Risk: natural 2 on survival in military/Party → SOC halved and status revoked.'}
          </div>
        </div>
        ${!character.solomani_passing
          ? `<button class="btn ghost" id="btn-passing-docs" style="font-size:11px;padding:6px 12px">OBTAIN DOCUMENTS (30,000 Cr)</button>`
          : ''
        }
      </div>
    </div>
  ` : '';

  return `
    ${hfTrainingBanner}
    <h3 style="margin-top:${hfTrainingBanner ? '0' : '28'}px;font-family:var(--font-mono);font-size:11px;letter-spacing:0.3em;color:var(--amber-dim);text-transform:uppercase">Choose an Assignment</h3>
    <div class="card-grid">${cards}</div>
    ${coverPickerHTML}
    ${homeForcesHTML}
    ${solsecMonitorHTML}
    ${passingDocsHTML}
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
        <span class="stable-name">${esc(t.name || key)}${t.requires_edu ? ` <span class="stable-req">(EDU ${t.requires_edu}+)</span>` : ''}</span>
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

    // Passing documents exposure notice
    const exposedHTML = lr.passing_exposed ? `
      <div class="event-box" style="border-color:var(--danger);margin-top:10px;background:rgba(200,50,50,0.08)">
        <span class="event-label" style="color:var(--danger);font-size:13px">PASSING DOCUMENTS EXPOSED</span>
        <p style="margin:4px 0 0;font-size:12px;color:var(--text)">
          Your falsified genetic records were discovered (natural 2).
          SOC halved (rounded down). Passing status permanently revoked.
          Career ends without Benefit rolls.
        </p>
      </div>` : '';

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
        ${exposedHTML}
        ${ana2HTML}
        ${parallelNotice}
        <p class="phase-body">${survived
          ? 'Your term continues. Roll the Event table to see what the last four years brought.'
          : lr.mishapNoEject
            ? 'A mishap struck — but you stay in the career. Roll on the Mishap table to see what happened.'
            : 'Your career is over. Roll on the Mishap table to see how it ended.'}</p>
        <div class="phase-actions">
          <button class="btn ${survived ? 'primary' : 'danger'}" id="btn-post-survive">
            ${survived ? 'ROLL EVENT →' : 'ROLL MISHAP →'}
          </button>
        </div>
      </div>
    `;
  }

  // Storm Knight Heroism selector
  const _STORM_KNIGHT_IDS = new Set(['storm_knight_thunder', 'storm_knight_inconstant_star', 'storm_knight_shadows']);
  const isStormKnight = _STORM_KNIGHT_IDS.has(career.id);
  const heroismDM = character.storm_knight_heroism_dm || 0;

  const heroismHTML = isStormKnight ? `
    <div style="margin:14px 0 4px;padding:12px 14px;border:1px solid var(--border);border-radius:6px">
      <div style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim);margin-bottom:8px">STORM KNIGHT — HEROISM RULE</div>
      <p style="font-size:12px;color:var(--text-dim);margin:0 0 10px">
        You may voluntarily accept a negative DM to your survival roll. If you survive, your Events roll gains an equal positive DM.
        DM−1 = Heroism. DM−2 = Grand Heroism. This choice must be made before rolling.
      </p>
      <div style="display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn ${heroismDM === 0 ? 'primary' : 'ghost'} btn-heroism-choice" data-dm="0"
          style="font-size:11px;padding:6px 12px">NO HEROISM (DM±0)</button>
        <button class="btn ${heroismDM === -1 ? 'primary' : 'ghost'} btn-heroism-choice" data-dm="-1"
          style="font-size:11px;padding:6px 12px">HEROISM (DM−1)</button>
        <button class="btn ${heroismDM === -2 ? 'primary' : 'ghost'} btn-heroism-choice" data-dm="-2"
          style="font-size:11px;padding:6px 12px">GRAND HEROISM (DM−2)</button>
      </div>
      ${heroismDM !== 0 ? `<p style="font-size:11px;color:var(--amber);margin:8px 0 0">
        Heroism active — survival DM${heroismDM > 0 ? '+' : ''}${heroismDM}.
        If you survive, your Event roll gains DM+${Math.abs(heroismDM)}.
      </p>` : ''}
    </div>
  ` : '';

  return `
    <div class="stage-content">
      <div class="phase-label">Will You Survive?</div>
      <h2 class="phase-title">Survival Roll</h2>
      <p class="phase-subtitle">${s.characteristic} ${s.target}+ (your DM is ${formatDM(dm)}${isStormKnight && heroismDM !== 0 ? `, Heroism DM${heroismDM}` : ''})</p>

      <p class="phase-body">Fail this roll and you suffer a career-ending mishap. Welcome to Traveller.</p>

      ${heroismHTML}

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
  if (/any\s+(?:one\s+)?skill\s+you\s+(?:already\s+have|possess)/i.test(text)
      || /any\s+skill\s+of\s+your\s+choice/i.test(text)
      || /gain\s+(?:(?:one|a)\s+level\s+(?:in|of)\s+)?any\s+(?:skill|service\s+skill)/i.test(text)
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

  // Pattern 4d: "increase any one of the following skills you already possess by
  // one level: X, Y or Z" (bounty_hunter[6])
  m = text.match(/increase\s+any\s+one\s+of\s+(?:the\s+)?following\s+skills[^:]*:\s*([^.]+?)(?:\.|if\s+you|$)/i);
  if (m) {
    const parts = splitToParts(m[1].trim());
    if (parts.length >= 1) return parts;
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
  // Support "Skill (Speciality)" as a single string when speciality arg is absent
  let lname = (skillName || '').toLowerCase();
  let lspec = speciality ? speciality.toLowerCase() : null;
  if (!lspec) {
    const m = lname.match(/^(.+?) \((.+)\)$/);
    if (m) { lname = m[1]; lspec = m[2]; }
  }
  for (const s of skills) {
    if (s.name.toLowerCase() !== lname) continue;
    if (lspec && s.speciality && s.speciality.toLowerCase() === lspec) return s.level;
    if (!lspec && !s.speciality) return Math.max(s.level || 0, 0);
  }
  // Check if it's a characteristic name (STR/DEX/etc.) — use the stat DM.
  const CHAR_KEYS = ['STR','DEX','END','INT','EDU','SOC'];
  const upper = skillName.toUpperCase();
  if (CHAR_KEYS.includes(upper)) {
    const stat = character?.characteristics?.[upper] ?? 7;
    return charDM(stat);
  }
  // Aliases: RES (Hiver Resolve) → SOC; PSI → psi; REP → reputation
  if (upper === 'RES') return charDM(character?.characteristics?.SOC ?? 7);
  if (upper === 'PSI') return charDM(character?.psi ?? 0);
  if (upper === 'REP') return charDM(character?.reputation ?? 0);
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

// ─── Life event choice UI builder ─────────────────────────────────────────────
// Returns { title, body, buttons } where buttons is HTML using btn-life-choice-{value}
// for precareer context or btn-career-life-choice-{value} for career context.
function buildLifeEventChoiceUI(kind, pending, context) {
  const prefix = context === 'career' ? 'btn-career-life-choice-' : 'btn-life-choice-';
  const hasBenefits = !!(pending.has_benefits);
  const hasBenefitRolls = (character.pending_benefit_rolls || 0) > 0;

  let title = 'Life Event Choice';
  let body = 'An unexpected event requires a decision.';
  let buttons = '';

  if (kind === 'romantic_split') {
    title = 'Life Event — Relationship Ends Badly';
    body = 'A romantic relationship involving you ends badly. Choose the consequence:';
    buttons = `
      <button class="card" id="${prefix}rival">
        <div class="card-title">Rival [Romantic]</div>
        <div class="card-desc">They become a rival — someone who competes with or resents you.</div>
      </button>
      <button class="card" id="${prefix}enemy">
        <div class="card-title">Enemy [Romantic]</div>
        <div class="card-desc">They become an enemy — actively working against you.</div>
      </button>`;

  } else if (kind === 'racial_incident') {
    title = 'Life Event — Racial Incident';
    body = 'A relationship in your life suffers as a result of the incident. Choose the consequence:';
    buttons = `
      <button class="card" id="${prefix}rival">
        <div class="card-title">Rival</div>
        <div class="card-desc">They become a rival — someone who resents or competes with you.</div>
      </button>
      <button class="card" id="${prefix}enemy">
        <div class="card-title">Enemy</div>
        <div class="card-desc">They become an active enemy — seriously working against you.</div>
      </button>`;

  } else if (kind === 'betrayal_no_associates') {
    title = 'Life Event — Betrayal';
    body = 'A friend has betrayed you. You have no existing Contacts or Allies to convert. Gain one of:';
    buttons = `
      <button class="card" id="${prefix}rival">
        <div class="card-title">Rival [Betrayer]</div>
        <div class="card-desc">They become a rival — someone who resents or opposes you.</div>
      </button>
      <button class="card" id="${prefix}enemy">
        <div class="card-title">Enemy [Betrayer]</div>
        <div class="card-desc">They become an active enemy — a serious, ongoing threat.</div>
      </button>`;

  } else if (kind === 'crime_choice') {
    title = 'Life Event — Crime';
    body = 'You commit or are accused of a crime. Choose your consequence:';
    buttons = `
      <button class="card ${hasBenefitRolls ? '' : 'locked'}" id="${prefix}lose_benefit" ${hasBenefitRolls ? '' : 'disabled'}>
        <div class="card-title">Lose a Benefit Roll ${hasBenefitRolls ? '' : '(none available)'}</div>
        <div class="card-desc">You pay a fine or bribe. Lose one mustering-out benefit roll.</div>
      </button>
      <button class="card" id="${prefix}prisoner">
        <div class="card-title">Take the Prisoner Career</div>
        <div class="card-desc">You serve time. Your next career must be Prisoner.</div>
      </button>`;

  } else if (kind === 'drinax_arranged_marriage') {
    title = 'Life Event — Arranged Marriage';
    body = 'Your family arranges a marriage for you. You won\'t meet your new spouse until the ceremony. Accept for SOC +1, or decline.';
    buttons = `
      <button class="card" id="${prefix}accept">
        <div class="card-title">Accept (SOC +1)</div>
        <div class="card-desc">Go through with the marriage. Gain SOC +1.</div>
      </button>
      <button class="card" id="${prefix}decline">
        <div class="card-title">Decline</div>
        <div class="card-desc">Refuse the arrangement. No mechanical change.</div>
      </button>`;

  } else if (kind === 'drinax_star_guard') {
    title = 'Life Event — Star Guard Commission';
    body = 'You inherit a place in the Star Guard. Sell the commission for cash, or take it and enter the Navy.';
    buttons = `
      <button class="card" id="${prefix}sell">
        <div class="card-title">Sell the Commission</div>
        <div class="card-desc">Roll 1D × Cr10,000 — paid out immediately.</div>
      </button>
      <button class="card" id="${prefix}commission">
        <div class="card-title">Take the Commission (Navy)</div>
        <div class="card-desc">Auto-qualify for Navy; automatic promotion your first term (DM+12 to Advancement).</div>
      </button>`;

  } else if (kind === 'drinax_duel_penalty') {
    title = 'Life Event — Duel Penalty';
    body = 'The cheating duellist has hurt you. Choose one additional penalty to suffer:';
    buttons = `
      <button class="card ${hasBenefits ? '' : 'locked'}" id="${prefix}lose_benefit" ${hasBenefits ? '' : 'disabled'}>
        <div class="card-title">Lose 1 Benefit Roll ${hasBenefits ? '' : '(none available)'}</div>
        <div class="card-desc">Lose one mustering-out benefit roll.</div>
      </button>
      <button class="card" id="${prefix}lose_soc">
        <div class="card-title">Lose 1 SOC</div>
        <div class="card-desc">Your social standing suffers from the scandal.</div>
      </button>
      <button class="card" id="${prefix}lose_end">
        <div class="card-title">Lose 1 END</div>
        <div class="card-desc">You are wounded in the exchange.</div>
      </button>`;

  } else if (kind === 'drinax_child_crisis') {
    title = 'Life Event — Mouth to Feed';
    body = 'A child is born but the tribe cannot feed another. Choose what happens:';
    buttons = `
      <button class="card" id="${prefix}child_dies">
        <div class="card-title">The Child Dies</div>
        <div class="card-desc">A tragic outcome — narrative only, no mechanical penalty.</div>
      </button>
      <button class="card" id="${prefix}drifter">
        <div class="card-title">Leave — Drifter</div>
        <div class="card-desc">You strike out to provide for the child. Next career must be Drifter.</div>
      </button>
      <button class="card" id="${prefix}rogue">
        <div class="card-title">Leave — Rogue</div>
        <div class="card-desc">You turn to crime to provide for the child. Next career must be Rogue.</div>
      </button>`;

  } else if (kind === 'drinax_ship_berth') {
    title = 'Life Event — Ship Berth Offered';
    body = 'A merchant or smuggler offers you a place on their crew. Choose your path:';
    buttons = `
      <button class="card" id="${prefix}rogue">
        <div class="card-title">Join as Rogue</div>
        <div class="card-desc">Auto-qualify for the Rogue career next term.</div>
      </button>
      <button class="card" id="${prefix}merchant">
        <div class="card-title">Join as Merchant</div>
        <div class="card-desc">Auto-qualify for the Merchant career next term.</div>
      </button>
      <button class="card" id="${prefix}decline">
        <div class="card-title">Decline</div>
        <div class="card-desc">Stay where you are. No transfer.</div>
      </button>`;

  } else if (kind === 'asim_family_aid') {
    title = 'Life Event — Impoverished Family';
    body = 'Your family is struggling. You can give up a benefit roll to help them — and they\'ll owe you one.';
    buttons = `
      <button class="card ${hasBenefits ? '' : 'locked'}" id="${prefix}pay" ${hasBenefits ? '' : 'disabled'}>
        <div class="card-title">Help Them ${hasBenefits ? '' : '(no benefit rolls available)'}</div>
        <div class="card-desc">Lose 1 Benefit roll. Gain DM+1 to your next Advancement roll.</div>
      </button>
      <button class="card" id="${prefix}keep">
        <div class="card-title">Keep Your Distance</div>
        <div class="card-desc">No mechanical change. Family remains struggling.</div>
      </button>`;

  } else if (kind === 'asim_misfortune_choice') {
    title = 'Life Event — Dangerous Misunderstanding';
    body = 'You must pay a price. Lose a Benefit roll (if available), or sever ties with a Contact or Ally:';
    const assocOpts = (pending.contacts_allies || []).map(a =>
      `<button class="card" id="${prefix}lose_associate_${a.idx}">
        <div class="card-title">Lose ${a.kind.charAt(0).toUpperCase() + a.kind.slice(1)}</div>
        <div class="card-desc">${escapeHTML(a.description || a.kind)}</div>
      </button>`
    ).join('');
    const benefitBtn = hasBenefits
      ? `<button class="card" id="${prefix}lose_benefit">
          <div class="card-title">Lose 1 Benefit Roll</div>
          <div class="card-desc">Lose one mustering-out benefit roll.</div>
        </button>`
      : '';
    buttons = benefitBtn + assocOpts;
    if (!buttons) {
      title = 'Life Event — Dangerous Misunderstanding';
      body = 'A dangerous misunderstanding — no benefit rolls or associates to lose. Narrative consequence only.';
      buttons = `<button class="card" id="${prefix}lose_benefit" disabled>
        <div class="card-title">Nothing to lose</div>
        <div class="card-desc">No mechanical penalty available.</div>
      </button>`;
    }
  }

  return { title, body, buttons };
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
    const _eShowPicker = !_eChosen && !lr.pendingEventChoice && !lr.eventChoiceResolved && (
      (_ePickerOpts && _ePickerOpts.length > 0) ||
      (_eWild && (_eDmAlt || pendingGrants.length > 0)) ||
      (_eTransfer && !pendingGrants.length)  // transfer alone (no competing DM)
    );
    // DMs embedded as alternatives in the skill picker (prisoner[5] pattern)
    const pendingGrantsInPicker = _eShowPicker && pendingGrants.length > 0 && !_eDmAlt;
    // Competing rewards with no skill picker: DM vs DM, or DM vs transfer.
    // Suppress entirely when a pending_event_choice card-picker already owns the decision.
    const showDualChoice = !_eChosen && !_eShowPicker && !lr.pendingEventChoice && (
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
    ` : (!pendingGrantsInPicker && !lr.pendingEventChoice && pendingGrants.length) ? `
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
    // Suppressed when the backend supplied a structured pending_event_choice
    // (e.g. bounty_hunter[9]) — that skill_check is authoritative and applies
    // its own on_pass/on_fail server-side; rendering this text-parsed picker too
    // would let the player roll the same check twice with conflicting outcomes.
    const contested = !chosenPath && !lr.eventContestedResolved && !lr.pendingEventChoice
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
    // When a pending_choice handler owns all associate grants, skip text-parsed
    // ops entirely — the choice resolver auto-applies them and shows them in
    // auto_applied messages, so a picker here would create duplicates.
    const rawAssociateOps = lr.suppressAssocOps ? [] : parseEventAssociateOps(_assocSourceText);
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
            const isSolomani = character.society_id === 'solomani_confederation';
            return `
              <div class="assoc-op" data-assoc-op-idx="${idx}">
                <div class="assoc-op-prompt">${prompt}</div>
                <div class="assoc-input-row">
                  <input type="text" class="assoc-desc-input" data-assoc-desc="${idx}" placeholder="Who are they? (name or short note — optional)" />
                  ${isSolomani ? `<button class="skill-chip assoc-gen-btn" data-solomani-gen="${idx}" title="Roll D66 on the Solomani Contacts table and generate a name">⚄ Generate</button>` : ''}
                </div>
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
                <div class="assoc-input-row">
                  <input type="text" class="assoc-desc-input" data-assoc-desc="${idx}" placeholder="Who are they? (name or short note — optional)" />
                  ${character.society_id === 'solomani_confederation' ? `<button class="skill-chip assoc-gen-btn" data-solomani-gen="${idx}" title="Roll D66 on the Solomani Contacts table and generate a name">⚄ Generate</button>` : ''}
                </div>
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
    // Suppress the text-parsed mishap path when the structured trigger_disaster_mishap
    // effect already rolled the table — lr.disasterMishap holds that result and the
    // career-continues flag is already set on the character by the Python backend.
    const forcesMishap = rawForcesMishap && !contestedSucceededForMishap && !lr.disasterMishap;
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
    const pendingEventChoice = lr.pendingEventChoice || null;

    // Render structured event effects (auto-applied skill grants, associates, etc.)
    const eventEffectsMsgs = Array.isArray(lr.eventEffects) ? lr.eventEffects : [];
    const eventEffectsHTML = eventEffectsMsgs.length ? `
      <div class="dm-applied-box">
        <span class="event-label">Auto-applied event effects</span>
        ${eventEffectsMsgs.map(m => {
          const isConversion = /converted to/i.test(m);
          return `<div class="dm-chip ${isConversion ? 'converted' : 'applied'}">${escapeHTML(m)}</div>`;
        }).join('')}
      </div>
    ` : '';

    // Render disaster mishap result (event 2 / trigger_disaster_mishap)
    const dm = lr.disasterMishap;
    const disasterMishapHTML = dm ? `
      <div class="mishap-box">
        <span class="event-label">Disaster! Mishap [1D=${dm.roll?.total ?? '?'}]</span>
        <p style="margin:4px 0">${escapeHTML(dm.mishap || '')}</p>
        ${dm.auto_applied && dm.auto_applied.length ? dm.auto_applied.map(m => `<div class="dm-chip applied">${escapeHTML(m)}</div>`).join('') : ''}
      </div>
    ` : '';

    // Render pending event choice (skill_choice, free_skill_choice, skill_check, pending_choice)
    let pendingEventChoiceHTML = '';
    if (pendingEventChoice && !lr.eventChoiceResolved) {
      const pec = pendingEventChoice;
      const pecType = pec.type || '';
      if (pecType === 'skill_choice') {
        pendingEventChoiceHTML = `
          <div class="event-skill-picker">
            <span class="event-label">Choose a skill</span>
            <p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>${escapeHTML(pec.prompt || 'Pick one skill to gain at level 1:')}</em></p>
            <div class="skill-picker">
              ${(pec.options || []).map(sk => `<button class="skill-chip event-choice-skill" data-event-choice-skill="${escapeHTML(sk)}">+ ${escapeHTML(sk)} 1</button>`).join('')}
            </div>
          </div>`;
      } else if (pecType === 'free_skill_choice') {
        pendingEventChoiceHTML = `
          <div class="event-skill-picker">
            <span class="event-label">Free skill choice</span>
            <p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>${escapeHTML(pec.prompt || 'Enter any skill name:')}</em></p>
            <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
              <input type="text" id="input-event-freeskill" style="background:var(--bg2);color:var(--fg);border:1px solid var(--border);padding:4px 8px;border-radius:4px" placeholder="Skill name" />
              <button class="btn" id="btn-event-freeskill-confirm">CONFIRM</button>
            </div>
          </div>`;
      } else if (pecType === 'skill_check') {
        pendingEventChoiceHTML = `
          <div class="event-skill-picker">
            <span class="event-label">Skill check required</span>
            <p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>${escapeHTML(pec.prompt || 'Pick which skill to roll:')}</em></p>
            <div class="skill-picker">
              ${(pec.skills || []).map((sk, i) => {
                const lvl = getSkillLevelFor(sk.name, sk.speciality);
                const lvlStr = lvl >= 0 ? `+${lvl}` : `${lvl}`;
                const label = sk.speciality ? `${sk.name} (${sk.speciality})` : sk.name;
                return `<button class="skill-chip event-choice-skillcheck" data-event-choice-skillcheck="${i}" data-skill-name="${escapeHTML(sk.name)}">Roll ${escapeHTML(label)} ${pec.target || 8}+ (your DM ${lvlStr})</button>`;
              }).join('')}
            </div>
          </div>`;
      } else if (pecType === 'pending_choice') {
        pendingEventChoiceHTML = `
          <div class="event-skill-picker">
            <span class="event-label">Choose your reward</span>
            <p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>${escapeHTML(pec.prompt || 'Pick one option:')}</em></p>
            <div class="skill-picker">
              ${(pec.options || []).map(opt => `<button class="skill-chip event-choice-pending" data-event-choice-option="${escapeHTML(opt.id)}">${escapeHTML(opt.label)}</button>`).join('')}
            </div>
          </div>`;
      }
    }

    // Inline life event choice (fires when event 7 produces a pending_life_event_choice)
    const pendingLifeEventChoice = character.pending_life_event_choice || null;
    let pendingCareerLifeEventHTML = '';
    if (pendingLifeEventChoice) {
      const { title: lecTitle, body: lecBody, buttons: lecButtons } = buildLifeEventChoiceUI(
        pendingLifeEventChoice.kind, pendingLifeEventChoice, 'career'
      );
      pendingCareerLifeEventHTML = `
        <div class="event-skill-picker">
          <span class="event-label">Life Event — Choose</span>
          <p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>${escapeHTML(lecTitle)}: ${escapeHTML(lecBody)}</em></p>
          <div class="card-grid" style="margin-top:8px">${lecButtons}</div>
        </div>`;
    }

    // Gate also on pending injury from an event-triggered mishap
    const eventMishapInjuryPending = !!(forcesMishap && lr.mishapFromEvent && character.pending_injury_choice);
    const gateAdvance = !!(showPicker && !chosenPath) || pendingMishapRoll || pendingAssocOps.length > 0
      || !!(csr && csr.success && csr.pendingSkillPick && !csr.skillChosen)
      || entertainerPending || citizenMishapPending
      || !!(pendingEventChoice && !lr.eventChoiceResolved)
      || !!pendingLifeEventChoice
      || eventMishapInjuryPending;

    // Action row varies by what's happening:
    // - Pending forced mishap roll: show ROLL MISHAP
    // - Forced mishap rolled, Frozen Watch or noEject: career continues (show CONTINUE)
    // - Forced mishap rolled, ejecting: career ENDS — show END CAREER
    // - Citizen ev8 survival failed: show mishap button (handled inline above)
    // - Normal flow: show ATTEMPT advancement
    const actionsHTML = pendingMishapRoll ? `
      <button class="btn danger" id="btn-event-forced-mishap">ROLL ON MISHAP TABLE →</button>
    ` : (forcesMishap && lr.mishapFromEvent && (lr.mishapFromEvent.frozenWatch || lr.mishapFromEvent.noEject)) ? `
      <button class="btn primary" id="btn-post-event"${gateAdvance ? ' disabled' : ''}>CONTINUE IN CAREER →</button>
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
        ${eventEffectsHTML}
        ${disasterMishapHTML}
        ${eventMishapInjuryPending ? (() => {
          const inj = character.pending_injury_choice;
          const choices = inj.choices || ['STR', 'DEX', 'END'];
          const statDescriptions = { STR: 'Strength', DEX: 'Dexterity', END: 'Endurance' };
          const cards = choices.map(stat => `
            <button class="card" id="btn-event-mishap-injury-stat-${stat}">
              <div class="card-title">${stat} — ${statDescriptions[stat] || stat}</div>
              <div class="card-meta">Current: ${character.characteristics[stat] ?? '?'}</div>
              <div class="card-desc">Damage: −${inj.damage_to_chosen}${inj.auto_reduce_others ? ` to ${stat}, −${inj.auto_reduce_others} to other two` : ''}. Then choose: accept stat loss (free) OR pay medical debt.</div>
            </button>`).join('');
          return `
            <div class="event-skill-picker" style="margin-top:14px">
              <span class="event-label">Injury — Choose Affected Stat</span>
              <p class="phase-body" style="margin-top:6px"><strong>${escapeHTML(inj.prompt || 'Choose which stat absorbs the damage.')}</strong></p>
              <p style="font-size:11px;color:var(--amber-dim)">Pick which stat takes the hit, then choose to accept the loss or pay to fix it.</p>
              <div class="card-grid">${cards}</div>
            </div>`;
        })() : ''}
        ${pendingEventChoiceHTML}
        ${pendingCareerLifeEventHTML}
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
      } else if (ptype === 'skill_loss_choice') {
        // Show all skills with level >= 1 as buttons the player can pick to lose a level
        const losableSkills = Object.entries(character.skills || {})
          .filter(([, v]) => v >= 1)
          .sort(([a], [b]) => a.localeCompare(b));
        if (losableSkills.length === 0) {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <p class="phase-body" style="color:var(--amber-dim)">No skills with level ≥ 1 — nothing to lose.</p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-skillloss-none">CONTINUE (NO SKILL TO LOSE)</button>
              </div>
            </div>`;
        } else {
          const opts = losableSkills.map(([sk, lv]) =>
            `<button class="btn" id="btn-mishap-skillloss-${escapeHTML(sk)}">${escapeHTML(sk)} (lv ${lv}→${lv - 1})</button>`
          ).join('');
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px;flex-wrap:wrap">${opts}</div>
            </div>`;
        }
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
        } else if (pid === 'party_mishap5_ally') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn primary" id="btn-mishap-party5ally-accept">GAIN ALLY</button>
                <button class="btn" id="btn-mishap-party5ally-decline">DECLINE</button>
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
        } else if (pid === 'aslan_brave_fight') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn primary" id="btn-mishap-brave-fight">FIGHT BRAVELY</button>
                <button class="btn danger" id="btn-mishap-brave-refuse">REFUSE — END CAREER</button>
              </div>
            </div>`;
        } else if (pid === 'aslan_mgmt_accused') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn danger" id="btn-mishap-mgmt-guilty">YES, I STOLE IT</button>
                <button class="btn primary" id="btn-mishap-mgmt-innocent">I'M INNOCENT — ROLL ADVOCATE</button>
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
        } else if (pid === 'ge_lose_associate_or_forfeit') {
          const opts = (pending.options || []);
          const btns = opts.map((o, i) => `
            <button class="btn" id="btn-mishap-lose-assoc-${i}"
              data-option-id="${escapeHTML(o.id)}">${escapeHTML(o.label)}</button>`).join('');
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px;flex-direction:column;align-items:flex-start">${btns}</div>
            </div>`;
        } else if (pid === 'aslan_scientist_leave') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn primary" id="btn-mishap-scientist-leave">LEAVE FOR HUMAN SPACE</button>
                <button class="btn" id="btn-mishap-scientist-accept">ACCEPT CAREER END</button>
              </div>
            </div>`;
        } else if (pid === 'ge_forced_career_choice') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-ge-landless">LANDLESS ONE</button>
                <button class="btn" id="btn-mishap-ge-outlaw">OUTLAW</button>
              </div>
            </div>`;
        } else if (pid === 'ge_hierate_capture') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-ge-return">RETURN TO EMPIRE</button>
                <button class="btn primary" id="btn-mishap-ge-stay">STAY IN HIERATE</button>
              </div>
            </div>`;
        } else if (pid === 'ge_slave_revolt') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn danger" id="btn-mishap-slave-report">REPORT THE REVOLT</button>
                <button class="btn" id="btn-mishap-slave-allow">ALLOW IT</button>
              </div>
            </div>`;

        // ---- Vargr pending_choice UI ----
        } else if (pid === 'vargr_army_illegal_leader') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-vargrarmy-join">JOIN RING — ALLY + SOC −1</button>
                <button class="btn primary" id="btn-mishap-vargrarmy-testify">TESTIFY — SOC +1 + ENEMY</button>
              </div>
            </div>`;
        } else if (pid === 'vargr_citizen_cooperate') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn primary" id="btn-mishap-vargrcitiaid">AID INVESTIGATION — DM+2 NEXT QUAL</button>
                <button class="btn" id="btn-mishap-vargrcitirefuse">REFUSE — GAIN ALLY</button>
              </div>
            </div>`;
        } else if (pid === 'vargr_corsair_betrayal') {
          const opts = (pending.options || []);
          const btns = opts.map((o, i) => `
            <button class="btn" id="btn-mishap-vargrbetray-${i}"
              data-option-id="${escapeHTML(o.id)}"
              data-assoc-idx="${o.associate_index ?? ''}">${escapeHTML(o.label)}</button>`).join('');
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px;flex-direction:column;align-items:flex-start">${btns}</div>
            </div>`;
        } else if (pid === 'vargr_law_deal') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn" id="btn-mishap-vargrlaw-accept">ACCEPT DEAL — FORCED OUT + SOC −1</button>
                <button class="btn danger" id="btn-mishap-vargrlaw-refuse">REFUSE — INJURY + ENEMY</button>
              </div>
            </div>`;
        } else if (pid === 'vargr_scientist_funding') {
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px">
                <button class="btn primary" id="btn-mishap-vargrsci-stay">STAY QUIETLY — CONTINUE, NO BENEFIT</button>
                <button class="btn" id="btn-mishap-vargrsci-roll">ROLL SOC 8+ — NEW PACK</button>
              </div>
            </div>`;

        } else if ((pending.options || []).length > 0) {
          // Generic fallback: render any pending_choice with an options array as buttons.
          // Each option sends { option_id: opt.id } to the Python resolver.
          const opts = (pending.options || []).map(opt =>
            `<button class="btn generic-pending-opt" data-option-id="${escapeHTML(opt.id)}">${escapeHTML(opt.label || opt.id)}</button>`
          ).join('');
          pendingHtml = `
            <div class="event-box" style="margin-top:14px">
              <p class="phase-body"><strong>${escapeHTML(pprompt)}</strong></p>
              <div class="phase-actions" style="margin-top:8px;flex-wrap:wrap">${opts}</div>
            </div>`;
        }
      } else if (ptype === 'skill_check') {
        const skills = (pending.skills || []).map(s => {
          const lvl = getSkillLevelFor(s.name, s.speciality);
          const lvlStr = lvl >= 0 ? `+${lvl}` : `${lvl}`;
          return `<button class="btn" id="btn-mishap-skillcheck-${escapeHTML(s.name)}"
            data-skill="${escapeHTML(s.name)}">Roll ${escapeHTML(s.name)} ${pending.target || 8}+ (DM ${lvlStr})</button>`;
        }).join('');
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
            <p class="small-hint" style="margin-top:8px;color:var(--muted)">${lr.mishapNoEject
              ? 'You remain in your career despite the mishap — you lose REP but continue serving.'
              : 'Career ends — no further mechanical effects apply.'}</p>
          ` : ''}
        </div>
        ${autoHtml}
        ${injDataHtml}
        ${pendingHtml}
        ${skillCheckHtml}
        ${injPickerHtml}
        ${injTreatmentHtml}
        ${(canEnd && !lr.mishapNoEject) ? anagathicsBoxHTML('btn-mishap-buy-anagathics') : ''}
        <div class="phase-actions" style="margin-top:16px">
          ${canEnd && lr.mishapNoEject
            ? `<button class="btn primary" id="btn-post-mishap-continue">CONTINUE IN CAREER →</button>`
            : canEnd
            ? `<button class="btn danger" id="btn-post-mishap">END CAREER →</button>`
            : ''}
        </div>
      </div>
    `;
  }

  const _noEject = uiState.pendingMishapNoEject || false;
  return `
    <div class="stage-content">
      <div class="phase-label">Mishap Table · 1D Roll</div>
      <h2 class="phase-title">${_noEject ? 'A Mishap Occurred' : 'You Failed to Survive'}</h2>
      <p class="phase-body">${_noEject
        ? 'This career\'s mishaps do not end your service — but you lose REP. Roll 1D to see what went wrong.'
        : 'A mishap ends your career. Roll 1D to see what went wrong.'}</p>
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
  const advDm = a.characteristic === 'REP'
    ? charDM(character.reputation || 0)
    : charDM(character.characteristics[a.characteristic]);

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
  const _igMustLeave = term.career_id === 'imperial_guard' && !!character.imperial_guard_must_leave;

  // Semi-career "try out" buttons — appear next to ANOTHER TERM when the character
  // is currently in a qualifying source career (and, for Guard, has been promoted).
  const _semiCareerLabels = {
    imperial_guard: 'TRY OUT FOR IMPERIAL GUARD',
    ini: 'TRY OUT FOR NAVAL INTELLIGENCE',
  };
  const _semiCareerBtns = CAREERS
    .filter(c => {
      if (!c.requires_source_career) return false;
      if (!c.requires_source_career.includes(term.career_id)) return false;
      if (c.requires_advancement && !term.advanced) return false;
      if ((character.banned_career_ids || []).includes(c.id)) return false;
      return true;
    })
    .map(c => {
      const label = _semiCareerLabels[c.id] || `TRY OUT FOR ${c.name.toUpperCase()}`;
      return `<button class="btn ghost btn-try-semi-career" data-semi-career="${c.id}">${escapeHTML(label)} →</button>`;
    })
    .join('');
  const _iniCareer = term.career_id === 'ini';
  const _iniReturnNote = _iniCareer ? `
    <div class="event-box" style="border-color:var(--accent);margin-top:10px;font-size:12px">
      <span class="event-label" style="color:var(--accent)">⚑ INI SERVICE</span>
      Naval rank frozen at ${character.ini_frozen_navy_rank ?? '?'} during INI service.
      You may return to ${esc(character.ini_source_career_id || 'Navy')} at any time — choose it
      in the career picker and you will be automatically accepted back at your held rank.
    </div>` : '';
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
  ` : _igMustLeave ? `
    <div class="event-box" style="border-color:var(--danger);margin-top:14px">
      <span class="event-label" style="color:var(--danger)">⚔ IMPERIAL GUARD — SERVICE ENDED</span>
      Advancement is required for continued Guard service. You must muster out or return to your
      source career (${esc(character.imperial_guard_source_career_id || 'Army/Marines')}).
    </div>
    <div class="phase-actions" style="margin-top:12px">
      <button class="btn" id="btn-leave-career">MUSTER OUT</button>
    </div>
    ${anagathicsBoxHTML('btn-advance-buy-anagathics')}
  ` : `
    ${_iniReturnNote}
    <div class="phase-actions">
      <button class="btn primary" id="btn-next-term">ANOTHER TERM →</button>
      ${_semiCareerBtns}
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
            ? `Commissioned! Rank 1${lr.newRankTitle ? ` — ${esc(lr.newRankTitle)}` : ''}`
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
        return `<button class="btn skill-table-btn ${gated ? 'ghost' : ''}" data-adv-skill-table="${key}" ${gated ? 'disabled' : ''}><span class="stable-name">${esc(t.name || key)}${t.requires_edu ? ` <span class="stable-req">(EDU ${t.requires_edu}+)</span>` : ''}</span>${previewItems ? `<span class="stable-preview">${previewItems}</span>` : ''}</button>`;
      }).join('');
      return `
        <div class="stage-content">
          <div class="phase-label">Advancement — Promoted · Bonus Skill Roll</div>
          <h2 class="phase-title">Promoted to Rank ${lr.newRank}${lr.newRankTitle ? ` — ${esc(lr.newRankTitle)}` : ''}</h2>
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
          ? `Promoted to Rank ${lr.newRank}${lr.newRankTitle ? ` — ${esc(lr.newRankTitle)}` : ''}`
          : 'No Advancement This Term'}</h2>
        ${rollReadoutHTML(lr.data, { label: `${a.characteristic} ${a.target}+` })}
        ${(advanced && lr.rankBonus) ? `
          <div class="event-box" style="border-color:var(--success,#7fd87f);margin-top:10px">
            <span class="event-label" style="color:var(--success,#7fd87f)">RANK BONUS APPLIED</span>
            ${escapeHTML(lr.rankBonus)}
          </div>` : ''}
        ${lr.knightGrandCross ? `
          <div class="event-box" style="border-color:var(--accent);margin-top:10px;background:rgba(100,180,255,0.07)">
            <span class="event-label" style="color:var(--accent);font-size:13px">⚔ KNIGHT GRAND CROSS COMMANDER</span>
            <p style="margin:4px 0 0;font-size:12px;color:var(--text)">You have achieved the highest rank of honour in your Order. SOC raised to minimum 12. Awarded: Grand Cross Medallion and Grand Cross Sash.</p>
          </div>` : (lr.knightCommanderByRank ? `
          <div class="event-box" style="border-color:var(--accent);margin-top:10px;background:rgba(100,180,255,0.07)">
            <span class="event-label" style="color:var(--accent);font-size:13px">⚔ KNIGHT COMMANDER BY RANK</span>
            <p style="margin:4px 0 0;font-size:12px;color:var(--text)">You have attained the highest rank in your Order. SOC raised to minimum 10 (or 11 if also By Deed). Awarded: Medallion of the Order, White Sash of Honour, Sword of Honour.</p>
          </div>` : '')}
        ${lr.advancementSkillGained ? `
          <div class="event-box" style="border-color:var(--success,#7fd87f);margin-top:10px">
            <span class="event-label" style="color:var(--success,#7fd87f)">BONUS SKILL GAINED</span>
            ${escapeHTML(lr.advancementSkillGained)}
          </div>` : ''}
        ${uiState.pendingCareerSpecialty ? `
          <div class="event-box" style="border-color:var(--amber);margin-top:10px">
            <span class="event-label" style="color:var(--amber)">CHOOSE SPECIALTY</span>
            <p style="font-size:12px;color:var(--text-dim);margin:4px 0 8px">${escapeHTML(uiState.pendingCareerSpecialty.skillName)} requires a specialty. Pick one to finish the term:</p>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
              ${(CASCADE_SKILLS[uiState.pendingCareerSpecialty.skillName] || []).map(s => `<button class="btn ghost specialty-chip" data-career-specialty="${escapeHTML(s)}">${escapeHTML(s)}</button>`).join('')}
            </div>
          </div>
        ` : `
        <p class="phase-body">You've completed Term ${term.overall_term_number}. Continue in this career or muster out?</p>
        ${advDecideActions}`}
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
      <h2 class="phase-title">${term.commissioned ? `Commissioned — Rank ${term.rank}${term.rank_title ? ` — ${esc(term.rank_title)}` : ''}` : term.advanced ? `Promoted to Rank ${term.rank}${term.rank_title ? ` — ${esc(term.rank_title)}` : ''}` : 'No Promotion This Term'}</h2>
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
        ? `You advanced to rank <strong>${term.rank}</strong>${term.rank_title ? ` — <strong>${esc(term.rank_title)}</strong>` : ''}.`
        : "You didn't advance this term."}</p>
      ${character.total_terms + 1 >= 4 ? `
        <p class="phase-body" style="color:var(--danger);font-style:italic">
          ⚠ Ending this next term will trigger an Aging roll. The older your Traveller, the heavier it hits.
        </p>
      ` : ''}
      ${forcedNext ? `
        <div class="event-box" style="border-color:var(--danger);margin-top:14px">
          <span class="event-label" style="color:var(--danger)">⚠ MANDATORY — ${esc(forcedNextName).toUpperCase()}</span>
          A conviction (or equivalent) forces you into the <strong>${esc(forcedNextName)}</strong> career next term.
          You cannot muster out or continue in your current career — you must serve your sentence first.
        </div>
        <div class="phase-actions" style="margin-top:12px">
          <button class="btn danger" id="btn-enter-forced-career">SERVE YOUR SENTENCE →</button>
        </div>
      ` : `
        <div class="phase-actions">
          <button class="btn primary" id="btn-next-term">ANOTHER TERM IN ${esc(career.name).toUpperCase()}</button>
          <button class="btn" id="btn-leave-career">MUSTER OUT OF ${esc(career.name).toUpperCase()}</button>
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

function _musterChoiceButtons(choice) {
  // Render choice buttons for a pending_muster_benefit_choice.
  // Uses "labels" for display when present (reroll type), falls back to option string.
  return choice.options.map((opt, i) => {
    const label = (choice.labels && choice.labels[i]) ? choice.labels[i] : opt;
    return `<button class="btn primary btn-muster-skill-choice" data-skill="${escapeHTML(opt)}">${escapeHTML(label)} →</button>`;
  }).join('');
}

// Naming UI for associates granted by a mustering-out benefit roll — reuses the
// same D66 personage + species-name generator offered during career events.
function musterAssocNamingHTML(newAssociates) {
  const list = Array.isArray(newAssociates) ? newAssociates : [];
  if (!list.length) return '';
  const labelAssoc = (k) => ({ contact: 'Contact', ally: 'Ally', rival: 'Rival', enemy: 'Enemy' }[k] || k);
  const rows = list.map(a => {
    const cur = (character.associates && character.associates[a.index]) || a;
    return `
      <div class="muster-assoc-row">
        <span class="assoc-label assoc-kind-${escapeAttr(a.kind)}">[${labelAssoc(a.kind)}]</span>
        <input type="text" class="muster-assoc-input" data-assoc-index="${a.index}"
               value="${escapeAttr(cur.description || '')}" placeholder="Type and name — e.g. Corrupt Politician — Nina Moussa" />
        <button class="btn ghost muster-assoc-gen" data-assoc-index="${a.index}" title="Generate a random type and name">🎲 Generate</button>
      </div>`;
  }).join('');
  return `
    <div class="event-skill-picker" style="margin-top:12px">
      <span class="event-label">Name your new ${list.length === 1 ? 'associate' : 'associates'}</span>
      <p class="picker-status" style="margin:0 0 8px 0;color:var(--amber-dim)"><em>Generate a type + name, or type your own. Saved automatically.</em></p>
      ${rows}
    </div>`;
}

// Cascade parent skills held above level 0 without a specialty — an invalid
// state in MgT (e.g. "Gun Combat 2"). These need their level moved into a
// chosen specialty at character completion.
function invalidCascadeParents() {
  return (character.skills || []).filter(s =>
    s && s.speciality == null && (s.level || 0) > 0 && CASCADE_SKILLS[s.name]
  );
}

function renderCascadeCleanup() {
  const invalid = invalidCascadeParents();
  if (!invalid.length) {
    return `
      <div class="panel-header"><span class="led"></span><span>SKILL CLEANUP</span></div>
      <div class="stage-content">
        <h2 class="phase-title">Specialties Clean</h2>
        <p class="phase-body">No cascade skills need a specialty — your Traveller is good to go.</p>
        <div class="phase-actions" style="margin-top:16px">
          <button class="btn primary" id="btn-cascade-cancel">← BACK</button>
        </div>
      </div>`;
  }
  const choices = uiState.cascadeCleanupChoices || {};
  const rows = invalid.map(s => {
    const opts = CASCADE_SKILLS[s.name] || [];
    const chosen = choices[s.name];
    return `
      <div class="event-skill-picker" style="margin-top:10px">
        <span class="event-label">${escapeHTML(s.name)} ${s.level} — choose a specialty</span>
        <p class="picker-status" style="margin:0 0 6px 0;color:var(--amber-dim)"><em>Level ${s.level} moves into your chosen ${escapeHTML(s.name)} specialty; the base skill drops to 0.</em></p>
        <div class="skill-picker">
          ${opts.map(o => `<button class="skill-chip cascade-cleanup-opt${chosen === o ? ' selected' : ''}" data-cleanup-skill="${escapeAttr(s.name)}" data-cleanup-spec="${escapeAttr(o)}">${escapeHTML(o)}${chosen === o ? ' ✓' : ''}</button>`).join('')}
        </div>
      </div>`;
  }).join('');
  const allChosen = invalid.every(s => choices[s.name]);
  return `
    <div class="panel-header"><span class="led"></span><span>SKILL CLEANUP</span></div>
    <div class="stage-content">
      <div class="phase-label">Cleanup · Cascade Specialties</div>
      <h2 class="phase-title">Assign Cascade Specialties</h2>
      <p class="phase-body">These skills are held above level 0 without a specialty. In Traveller a cascade skill (Gun Combat, Pilot, Melee, …) sits at level 0 as the parent — pick which specialty each level belongs to.</p>
      ${rows}
      <div class="phase-actions" style="margin-top:16px">
        <button class="btn primary" id="btn-cascade-apply" ${allChosen ? '' : 'disabled'}>APPLY SPECIALTIES →</button>
        <button class="btn ghost" id="btn-cascade-cancel">CANCEL</button>
      </div>
    </div>`;
}

function renderMusterPhase() {
  if (uiState.cascadeCleanupMode) return renderCascadeCleanup();
  const careers = character.completed_careers;
  const rolls = character.pending_benefit_rolls;
  const cashRolled = character.cash_rolls_used;

  // If there is a pending benefit choice but NO lastRoll in memory — the player
  // refreshed the page mid-choice. Show the choice UI to recover gracefully.
  const livePendingChoice = character.pending_muster_benefit_choice;
  if (livePendingChoice && !uiState.lastRoll) {
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
      <div class="stage-content">
        <div class="phase-label">Benefit Choice Pending</div>
        <h2 class="phase-title">${escapeHTML(livePendingChoice.benefit || livePendingChoice.raw || 'Choose Your Benefit')}</h2>
        <p class="phase-body">${escapeHTML(livePendingChoice.prompt || 'Choose one option:')}</p>
        <div class="phase-actions" style="flex-wrap:wrap">
          ${_musterChoiceButtons(livePendingChoice)}
        </div>
      </div>
    `;
  }

  // Post-roll view: show dice readout + what was gained, then wait for "CONTINUE"
  if (uiState.lastRoll?.type === 'muster') {
    const lr = uiState.lastRoll;
    const colLabel = lr.column === 'cash' ? 'Cash Roll' : 'Benefit Roll';
    // Skill/reroll choice: set when backend returns pending_skill_choice
    const pendingSkillChoice = lr.pendingSkillChoice;
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
      <div class="stage-content">
        <div class="phase-label">${colLabel} — ${lr.careerName || lr.careerId}</div>
        <h2 class="phase-title">${lr.column === 'cash' ? `Gained ${lr.result}` : `Benefit: ${lr.result}`}</h2>
        ${rollReadoutHTML(lr.data, { label: `${colLabel} (1D)`, showTarget: false })}
        ${lr.rankDm ? `
          <div class="dm-applied-box" style="margin-top:8px">
            <span class="event-label">Rank 5-6 bonus</span>
            <div class="dm-chip applied">DM+1 to all benefit rolls (highest rank reached 5-6)</div>
          </div>` : ''}
        ${pendingSkillChoice ? `
          <p class="phase-body" style="margin-top:12px">${escapeHTML(pendingSkillChoice.prompt || 'Choose your benefit:')}</p>
          <div class="phase-actions" style="flex-wrap:wrap">
            ${_musterChoiceButtons(pendingSkillChoice)}
          </div>
        ` : `
          ${musterAssocNamingHTML(lr.newAssociates)}
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
    // If a forced career is still pending (e.g. crime conviction → prisoner), don't
    // finalize — route back to the career picker so the sentence can be served.
    if (character.forced_next_career_id) {
      const _forcedDef = CAREERS.find(c => c.id === character.forced_next_career_id);
      const _forcedName = _forcedDef?.name || character.forced_next_career_id;
      return `
        <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
        <div class="stage-content">
          <h2 class="phase-title">Benefits Claimed</h2>
          <div class="event-box" style="border-color:var(--danger);margin-top:14px">
            <span class="event-label" style="color:var(--danger)">⚠ MANDATORY SENTENCE — ${escapeHTML(_forcedName.toUpperCase())}</span>
            Mustering out complete. A conviction still requires you to serve a term in
            <strong>${escapeHTML(_forcedName)}</strong> before your career is over.
          </div>
          <div class="phase-actions" style="margin-top:16px">
            <button class="btn danger" id="btn-muster-to-forced-career">SERVE YOUR SENTENCE →</button>
          </div>
        </div>
      `;
    }

    const _exemptIds = new Set(['scout','rogue','prisoner','drifter']);
    const _qualTerms = (character.term_history || []).filter(h => !_exemptIds.has(h.career_id)).length;
    const _isSol = character.society_id === 'solomani_confederation';
    const _hasFullCareer = _isSol && (character.term_history || []).some(h => h.career_id === 'party' || h.career_id === 'solsec');
    const _pensionSub = _isSol
      ? (_hasFullCareer
          ? `${_qualTerms} qualifying term${_qualTerms===1?'':'s'}. Full rate (Party or SolSec service). Collectible at Class A–B starports in the Confederation; SolSec also at Class C.`
          : `${_qualTerms} qualifying term${_qualTerms===1?'':'s'}. Solomani Confederation rate — half the Imperial pension. Collectible at Class A–B starports within the Confederation.`)
      : `${_qualTerms} qualifying term${_qualTerms === 1 ? '' : 's'} of service (Scout, Rogue, Prisoner, and Drifter excluded).`;
    const pensionNote = character.pension_per_year > 0
      ? `<div style="margin-top:14px;padding:10px 14px;border:1px solid var(--amber-dim);border-radius:6px">
           <span style="font-size:11px;letter-spacing:0.15em;color:var(--amber-dim)">RETIREMENT PENSION</span>
           <div style="font-size:18px;font-family:var(--font-mono);color:var(--accent);margin-top:4px">
             Cr${character.pension_per_year.toLocaleString()}/year
           </div>
           <p style="font-size:11px;color:var(--text-dim);margin:4px 0 0">${_pensionSub}</p>
         </div>` : '';
    return `
      <div class="panel-header"><span class="led"></span><span>PHASE 05 — MUSTERING OUT</span></div>
      <div class="stage-content">
        <h2 class="phase-title">All Benefits Claimed</h2>
        <p class="phase-body">You've rolled all your mustering-out benefits. Your Traveller is ready.</p>
        ${pensionNote}
        ${invalidCascadeParents().length ? `
          <div class="event-box" style="border-color:var(--amber);margin-top:14px">
            <span class="event-label" style="color:var(--amber)">CASCADE SKILLS NEED SPECIALTIES</span>
            <p style="margin:4px 0 0;font-size:12px;color:var(--text)">${invalidCascadeParents().map(s => `${escapeHTML(s.name)} ${s.level}`).join(', ')} ${invalidCascadeParents().length === 1 ? 'is' : 'are'} held above level 0 with no specialty. Assign ${invalidCascadeParents().length === 1 ? 'it' : 'them'} before finishing.</p>
          </div>` : ''}
        <div class="phase-actions" style="margin-top:16px">
          ${invalidCascadeParents().length ? `<button class="btn" id="btn-cascade-cleanup">🧹 CLEAN UP SPECIALTIES (${invalidCascadeParents().length})</button>` : ''}
          <button class="btn primary" id="btn-finalize">FINALIZE CHARACTER →</button>
        </div>
      </div>
    `;
  }

  const careerPicker = careers.map((c, ci) => {
    const careerDef = CAREERS.find(x => x.id === c.career_id);
    const hasTable = careerDef?.mustering_out && Object.keys(careerDef.mustering_out).length > 0;
    const rollsUsed = c.benefit_rolls_used || 0;
    const maxRolls = c.benefit_rolls_earned || c.terms_served;  // earned includes rank bonus; fall back to terms for old saves
    const rollsLeft = maxRolls - rollsUsed;
    const rankBonus = maxRolls - c.terms_served;
    const exhausted = rollsLeft <= 0;
    const locked = !hasTable || exhausted;
    const selected = uiState.selectedMusterIndex === ci;
    const rollsDesc = rankBonus > 0
      ? `${c.terms_served} terms + ${rankBonus} rank bonus = ${maxRolls} total`
      : `${c.terms_served} term${c.terms_served === 1 ? '' : 's'}`;
    // Key by index, not career_id — the same career can be served more than once
    // (e.g. two Bounty Hunter stints), and a career_id key collapses them onto
    // the first record so the later stint's rolls can never be claimed.
    return `
      <button class="card ${locked ? 'locked' : ''} ${selected ? 'selected' : ''}" data-muster-career-index="${ci}" ${locked ? 'disabled' : ''}>
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

      ${(uiState.selectedMusterIndex != null && careers[uiState.selectedMusterIndex]) ? (() => {
        const selRec = careers[uiState.selectedMusterIndex];
        const selDef = CAREERS.find(x => x.id === selRec.career_id);
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

      <div class="phase-actions" style="margin-top:24px;border-top:1px solid var(--border);padding-top:16px">
        <button class="btn ghost" id="btn-forfeit-muster">LEAVE MUSTERING OUT →</button>
      </div>
    </div>
  `;
}

function wireMusterPhase() {
  document.querySelectorAll('[data-muster-career-index]').forEach(card => {
    card.addEventListener('click', () => {
      uiState.selectedMusterIndex = parseInt(card.dataset.musterCareerIndex, 10);
      renderStage();
    });
  });
  const btnForfeitMuster = document.getElementById('btn-forfeit-muster');
  if (btnForfeitMuster) {
    btnForfeitMuster.addEventListener('click', () => {
      if (!confirm('Leave mustering out? Any remaining rolls will be forfeited.')) return;
      character.pending_benefit_rolls = 0;
      saveCharacter();
      renderAll();
    });
  }

  const chkGoodFortune = document.getElementById('chk-good-fortune');
  if (chkGoodFortune) chkGoodFortune.addEventListener('change', () => {
    uiState.useGoodFortune = chkGoodFortune.checked;
    renderStage();
  });
  const btnCash = document.getElementById('btn-roll-cash');
  if (btnCash) {
    btnCash.addEventListener('click', async () => {
      try {
        const careerIndex = uiState.selectedMusterIndex;
        const careerRec = character.completed_careers?.[careerIndex];
        const careerId = careerRec?.career_id;
        const careerDef = CAREERS.find(x => x.id === careerId);
        const response = await apiCall('/api/character/muster-out',
          { career_id: careerId, career_index: careerIndex, column: 'cash' });
        await applyResponse(response);
        // Auto-clear selection if this career has no rolls left after the roll
        const updatedRec = character.completed_careers?.[careerIndex];
        const updatedMax = updatedRec ? (updatedRec.benefit_rolls_earned || updatedRec.terms_served) : 0;
        const updatedRollsLeft = updatedRec ? (updatedMax - (updatedRec.benefit_rolls_used || 0)) : 0;
        if (updatedRollsLeft <= 0) uiState.selectedMusterIndex = null;
        uiState.lastRoll = {
          type: 'muster',
          column: 'cash',
          data: response.roll,
          result: response.result,
          remaining_rolls: response.remaining_rolls,
          rankDm: response.rank_dm || 0,
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
        const careerIndex = uiState.selectedMusterIndex;
        const careerRec = character.completed_careers?.[careerIndex];
        const careerId = careerRec?.career_id;
        const careerDef = CAREERS.find(x => x.id === careerId);
        const useGoodFortune = !!(uiState.useGoodFortune && character.good_fortune_benefit_dm > 0);
        const response = await apiCall('/api/character/muster-out',
          { career_id: careerId, career_index: careerIndex, column: 'benefit', use_good_fortune: useGoodFortune });
        await applyResponse(response);
        uiState.useGoodFortune = false;
        // Auto-clear selection if this career has no rolls left after the roll
        const updatedRec = character.completed_careers?.[careerIndex];
        const updatedMax = updatedRec ? (updatedRec.benefit_rolls_earned || updatedRec.terms_served) : 0;
        const updatedRollsLeft = updatedRec ? (updatedMax - (updatedRec.benefit_rolls_used || 0)) : 0;
        if (updatedRollsLeft <= 0) uiState.selectedMusterIndex = null;
        uiState.lastRoll = {
          type: 'muster',
          column: 'benefit',
          data: response.roll,
          result: response.result,
          remaining_rolls: response.remaining_rolls,
          rankDm: response.rank_dm || 0,
          good_fortune_used: response.good_fortune_used,
          careerId,
          careerName: careerDef?.name || careerId,
          pendingSkillChoice: response.pending_skill_choice || null,
          newAssociates: response.new_associates || [],
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
      uiState.selectedMusterIndex = null;
      renderStage();
    });
  }

  // Skill choice buttons — shown when benefit is "A 1 or B 1 or ..."
  document.querySelectorAll('.btn-muster-skill-choice').forEach(btn => {
    btn.addEventListener('click', async () => {
      const chosen = btn.dataset.skill;
      try {
        const response = await apiCall('/api/character/muster-benefit-choice', { chosen });
        await applyResponse(response);
        uiState.lastRoll = null;
        uiState.selectedMusterIndex = null;
        renderAll();
      } catch (e) {
        alert(e.message);
      }
    });
  });

  // Mustering-out associate naming: persist a description without re-rendering
  // (so the inputs keep focus/value while the player edits several in a row).
  const saveMusterAssoc = async (index, description) => {
    const desc = (description || '').trim();
    if (!desc) return;
    try {
      const response = await apiCall('/api/character/associate', {
        op: 'update', index, description: desc,
      });
      await applyResponse(response);   // updates character + sidebar, no stage re-render
    } catch (e) { /* keep the typed value; surface only hard errors */ console.warn(e); }
  };
  document.querySelectorAll('.muster-assoc-gen').forEach(btn => {
    btn.addEventListener('click', async () => {
      const index = parseInt(btn.getAttribute('data-assoc-index'), 10);
      const input = document.querySelector(`.muster-assoc-input[data-assoc-index="${index}"]`);
      if (!input) return;
      const d1 = Math.ceil(Math.random() * 6);
      const d2 = Math.ceil(Math.random() * 6);
      const personage = _SOL_CONTACTS[d1 * 10 + d2] || 'Unknown Personage';
      const name = generateSpeciesName(character.species_id || 'solomani_human');
      input.value = `${personage} — ${name}`;
      await saveMusterAssoc(index, input.value);
    });
  });
  document.querySelectorAll('.muster-assoc-input').forEach(input => {
    input.addEventListener('change', () => {
      const index = parseInt(input.getAttribute('data-assoc-index'), 10);
      saveMusterAssoc(index, input.value);
    });
  });

  // Forced-career sentence from muster-out (crime conviction, etc.)
  const btnMusterToForcedCareer = document.getElementById('btn-muster-to-forced-career');
  if (btnMusterToForcedCareer) {
    btnMusterToForcedCareer.addEventListener('click', () => {
      character.phase = 'career';
      uiState.lastRoll = null;
      uiState.subPhase = null;
      uiState.selectedCareer = null;
      uiState.selectedAssignment = null;
      saveCharacter();
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

  wireCascadeCleanup();
}

// Wiring for the cascade-specialty cleanup flow — shared by the muster-out and
// done screens (both can surface the CLEAN UP SPECIALTIES button + picker).
function wireCascadeCleanup() {
  const btnCascadeCleanup = document.getElementById('btn-cascade-cleanup');
  if (btnCascadeCleanup) {
    btnCascadeCleanup.addEventListener('click', () => {
      uiState.cascadeCleanupMode = true;
      uiState.cascadeCleanupChoices = {};
      renderStage();
    });
  }
  document.querySelectorAll('.cascade-cleanup-opt').forEach(btn => {
    btn.addEventListener('click', () => {
      const skill = btn.getAttribute('data-cleanup-skill');
      const spec = btn.getAttribute('data-cleanup-spec');
      uiState.cascadeCleanupChoices = uiState.cascadeCleanupChoices || {};
      uiState.cascadeCleanupChoices[skill] = spec;
      renderStage();
    });
  });
  const btnCascadeCancel = document.getElementById('btn-cascade-cancel');
  if (btnCascadeCancel) {
    btnCascadeCancel.addEventListener('click', () => {
      uiState.cascadeCleanupMode = false;
      renderStage();
    });
  }
  const btnCascadeApply = document.getElementById('btn-cascade-apply');
  if (btnCascadeApply) {
    btnCascadeApply.addEventListener('click', async () => {
      try {
        const response = await apiCall('/api/character/cleanup-cascade-specialties',
          { choices: uiState.cascadeCleanupChoices || {} });
        await applyResponse(response);
        uiState.cascadeCleanupMode = false;
        uiState.cascadeCleanupChoices = {};
        renderAll();
      } catch (e) { alert(e.message); }
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
  // ── Robot done phase ──────────────────────────────────────────────────────
  if (character.character_type === 'robot') {
    const cfg = robotNormalize(character.robot_config || {});
    const calc = calculateRobotConfig(cfg);
    const chars = robotFoundryChars(cfg, calc);
    const charCells = ['STR','DEX','END','INT','EDU','SOC'].map(k=>`
      <div class="robot-char-cell">
        <span class="robot-char-key">${k}</span>
        <span class="robot-char-val">${chars[k]||0}</span>
      </div>`).join('');
    return `
      <div class="panel-header"><span class="led"></span><span>ROBOT COMPLETE — ${escapeHTML(cfg.name||'New Robot')}</span></div>
      <div class="stage-content">
        <div class="phase-label">Construction Complete · TL${rbN(cfg.techLevel,12)}</div>
        <h2 class="phase-title">${escapeHTML(cfg.name||'New Robot')}</h2>
        <p class="phase-subtitle">${escapeHTML(cfg.purpose||'No purpose specified.')} Construction cost: ${rbFmtCr(calc.cost)}.</p>
        <div class="robot-char-grid">${charCells}</div>
        <div class="robot-summary-block">
          <h4>Frame</h4>
          <p>${calc.chassis?.name||'?'} / ${calc.locomotion?.name||'?'} · Hits ${calc.hits} · Protection +${calc.armor.protection} · Speed ${calc.tacticalSpeed}m · Endurance ${calc.endurance}h</p>
        </div>
        <div class="robot-summary-block">
          <h4>Brain</h4>
          <p>${calc.brain?.name||'?'} · INT ${calc.intellect.finalInt} · Computer/${calc.brain?.computer??0} · BW ${calc.bandwidth.used}/${calc.bandwidth.total}</p>
        </div>
        <div class="robot-summary-block">
          <h4>Skills</h4>
          <p>${calc.skills.map(sk=>`${sk.name}${sk.specialty?` (${sk.specialty})`:''} ${sk.level}`).join(', ')||'None'}</p>
        </div>
        <div class="robot-summary-block">
          <h4>Traits</h4>
          <p>${calc.traits.join(', ')||'None'}</p>
        </div>
        <div class="phase-actions" style="margin-top:14px">
          <button class="btn primary" id="btn-export-robot-foundry">⬇ EXPORT TO FOUNDRY</button>
          <button class="btn ghost" id="btn-export-prominent">EXPORT JSON</button>
          <button class="btn" id="btn-back-to-robot-build">← EDIT ROBOT</button>
        </div>
      </div>`;
  }

  // ── Normal (biological) done phase ─────────────────────────────────────────
  // Cascade-specialty cleanup takes over the screen when active.
  if (uiState.cascadeCleanupMode) return renderCascadeCleanup();

  const existingConns = (character.associates || []).filter(a => (a.description || '').startsWith('Connection: '));
  const _invalidCascade = invalidCascadeParents();

  return `
    <div class="panel-header"><span class="led"></span><span>PHASE 06 — READY FOR ADVENTURE</span></div>
    <div class="stage-content">
      <div class="phase-label">Character Complete · Age ${character.age} · ${character.total_terms} Terms</div>
      <h2 class="phase-title">Your Traveller Is Ready</h2>
      <p class="phase-subtitle">${escapeHTML(character.name || 'This Traveller')} has survived creation. Take the character sheet and meet your group at the starport.</p>

      <div class="phase-body">
        <p>Your character's full history is in the Mission Log. Export the JSON to save them, or import a different Traveller to continue work.</p>
      </div>

      ${_invalidCascade.length ? `
        <div class="done-card" style="border-color:var(--amber)">
          <h3 class="done-card-title" style="color:var(--amber)">🧹 Cascade Skills Need Specialties</h3>
          <p class="empty" style="margin-bottom:10px">${_invalidCascade.map(s => `${escapeHTML(s.name)} ${s.level}`).join(', ')} ${_invalidCascade.length === 1 ? 'is' : 'are'} held above level 0 without a specialty. In Traveller a cascade skill sits at level 0 as the parent — assign each level to a specialty.</p>
          <div class="phase-actions">
            <button class="btn primary" id="btn-cascade-cleanup">CLEAN UP SPECIALTIES (${_invalidCascade.length})</button>
          </div>
        </div>` : ''}

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

      ${(() => {
          if (!character.pension_per_year) return '';
          const exemptIds = new Set(['scout','rogue','prisoner','drifter']);
          const qualTerms = (character.term_history || []).filter(h => !exemptIds.has(h.career_id)).length;
          const isSol = character.society_id === 'solomani_confederation';
          const hasFullCareer = isSol && (character.term_history || []).some(h => h.career_id === 'party' || h.career_id === 'solsec');
          let collectionNote, rateNote;
          if (isSol) {
            collectionNote = hasFullCareer
              ? 'Collectible at Class A–B starports within the Solomani Confederation. SolSec officers may also collect at Class C starports.'
              : 'Collectible at Class A–B starports within the Solomani Confederation only.';
            rateNote = hasFullCareer
              ? 'Full Imperial rate — Party or SolSec service.'
              : 'Solomani Confederation rate (½ Imperial pension).';
          } else {
            collectionNote = 'Paid annually at any Class A or B starport.';
            rateNote = `${qualTerms} qualifying term${qualTerms === 1 ? '' : 's'} of service (Scout, Rogue, Prisoner, and Drifter excluded).`;
          }
          return `
            <div class="done-card">
              <h3 class="done-card-title">Retirement Pension</h3>
              <div style="font-size:22px;font-family:var(--font-mono);color:var(--accent);margin:6px 0 4px">
                Cr${character.pension_per_year.toLocaleString()}/year
              </div>
              <p class="empty">${rateNote}</p>
              <p class="empty">${collectionNote}</p>
            </div>`;
        })()}

      ${renderPsionicsCard()}

      <div class="phase-actions">
        <button class="btn ghost" id="btn-export-prominent">EXPORT JSON</button>
        <button class="btn ghost" id="btn-export-foundry">⬇ EXPORT TO FOUNDRY</button>
        <button class="btn" id="btn-back-careers">← BACK TO CAREERS</button>
      </div>

      <div class="done-card tas-sheet-card">
        <h3 class="done-card-title">Character Sheet</h3>
        <p class="empty" style="margin-bottom:10px">Interactive Mongoose Traveller 2e sheet — click a stat or skill to roll, track wounds, conditions, weapons and gear. Use your browser's Print command to print it.</p>
        <div id="tas-sheet-mount">${renderTASSheet()}</div>
      </div>
    </div>
  `;
}

// ============================================================
// Interactive Character Sheet (TAS Form — Mongoose Traveller 2e layout)
// Rendered inline in the done phase. Fully interactive play aid:
// click stats/skills to roll, track wounds & conditions, manage
// weapons/gear/people/psionics/notes. State persists on character.play_state.
// ============================================================

// Lazily initialise and return the interactive play-state bucket.
function tasPlay() {
  if (!character.play_state || typeof character.play_state !== 'object') {
    character.play_state = { dmg: {}, conditions: [], wielded: [], weapons: [], notes: '' };
  }
  const ps = character.play_state;
  ps.dmg = ps.dmg || {};            // { STR: n, DEX: n, END: n } — current damage taken
  ps.conditions = ps.conditions || [];
  ps.wielded = ps.wielded || [];     // weapon names currently in hand
  ps.weapons = ps.weapons || [];     // [{name, dmg, range}]
  if (typeof ps.notes !== 'string') ps.notes = '';
  return ps;
}

// Effective characteristic value after subtracting any current damage.
function tasStatVal(stat) {
  const base = (stat === 'PSI') ? (character.psi || 0)
             : (stat === 'REP') ? (character.reputation || 0)
             : (character.characteristics[stat] || 0);
  const dmg = (tasPlay().dmg[stat] || 0);
  return Math.max(0, base - dmg);
}

// Show a transient roll-result toast in the corner.
function tasToast(html, kind) {
  let t = document.getElementById('tas-toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'tas-toast';
    t.className = 'tas-toast';
    document.body.appendChild(t);
  }
  t.className = 'tas-toast ' + (kind || '');
  t.innerHTML = html;
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 4200);
}

// Roll 2D6 + modifier, return {d1, d2, raw, total, mod}.
function tasRoll2D(mod) {
  const d1 = 1 + Math.floor(Math.random() * 6);
  const d2 = 1 + Math.floor(Math.random() * 6);
  return { d1, d2, raw: d1 + d2, total: d1 + d2 + (mod || 0), mod: mod || 0 };
}

// Click-to-roll a characteristic check.
function tasRollStat(stat) {
  const dm = charDM(tasStatVal(stat));
  const r = tasRoll2D(dm);
  tasToast(
    `<strong>${stat} check</strong> · 2D6 [${r.d1}+${r.d2}] ${formatDM(dm)} = <span class="tas-toast-total">${r.total}</span>`,
    'roll'
  );
}

// Click-to-roll a skill check (2D6 + relevant characteristic DM + skill level).
// For untrained skills the level is -3 (unskilled penalty).
function tasRollSkill(skillName, level, statForSkill) {
  const trained = level != null;
  const lvl = trained ? level : -3;
  const dm = statForSkill ? charDM(tasStatVal(statForSkill)) : 0;
  const r = tasRoll2D(dm + lvl);
  const lvlStr = trained ? `skill ${formatDM(lvl)}` : 'unskilled −3';
  const statStr = statForSkill ? ` · ${statForSkill} ${formatDM(dm)}` : '';
  tasToast(
    `<strong>${escapeHTML(skillName)}</strong> · 2D6 [${r.d1}+${r.d2}]${statStr} · ${lvlStr} = <span class="tas-toast-total">${r.total}</span>`,
    'roll'
  );
}

// Re-render just the sheet mount and re-wire it (keeps the rest of the page stable).
function refreshTASSheet() {
  saveCharacter();
  const mount = document.getElementById('tas-sheet-mount');
  if (mount) {
    mount.innerHTML = renderTASSheet();
    wireTASSheet();
  }
  // Keep the left character file panel in sync (stats/credits may have changed).
  try { renderSheet(); } catch (e) {}
}

// Build a lookup of the character's trained skills.
// Returns { base: { "Admin": level }, spec: { "Gun Combat": { "Slug": level } } }
function tasSkillIndex() {
  const base = {}, spec = {};
  (character.skills || []).forEach(s => {
    if (!s || s.name == null) return;          // skip null / malformed entries
    const lvl = (s.level == null) ? 0 : s.level;
    if (s.speciality) {
      spec[s.name] = spec[s.name] || {};
      spec[s.name][s.speciality] = lvl;
    } else {
      base[s.name] = lvl;
    }
  });
  return { base, spec };
}

// Suggested characteristic for each skill's default roll (MGT2e common usage).
const TAS_SKILL_STAT = {
  'Admin':'INT','Advocate':'SOC','Astrogation':'EDU','Athletics':'DEX','Animals':'INT',
  'Art':'INT','Broker':'INT','Carouse':'SOC','Deception':'INT','Diplomat':'SOC',
  'Drive':'DEX','Electronics':'INT','Engineer':'INT','Explosives':'EDU','Flyer':'DEX',
  'Gambler':'INT','Gun Combat':'DEX','Gunner':'INT','Heavy Weapons':'DEX','Investigate':'INT',
  'Jack-of-All-Trades':'INT','Language':'EDU','Leadership':'SOC','Mechanic':'INT','Medic':'EDU',
  'Melee':'STR','Navigation':'INT','Persuade':'SOC','Pilot':'DEX','Profession':'EDU',
  'Recon':'INT','Science':'EDU','Seafarer':'DEX','Sensors':'INT','Stealth':'DEX',
  'Steward':'INT','Streetwise':'INT','Survival':'EDU','Tactics':'INT','Vacc Suit':'DEX'
};

// Render one skill cell (base skill or a specialty line).
// isSpec=true marks a specialty so it can be visually indented under its parent.
function tasSkillCell(displayName, rollName, level, statForSkill, isSpec) {
  const trained = level != null;
  const lvlBadge = trained ? `<span class="tas-skill-lvl">${level}</span>` : `<span class="tas-skill-lvl untrained">−</span>`;
  return `<button class="tas-skill ${trained ? 'trained' : 'untrained'}${isSpec ? ' spec' : ''}"
      data-skill-roll="${escapeAttr(rollName)}"
      data-skill-level="${trained ? level : ''}"
      data-skill-stat="${statForSkill || ''}"
      title="Click to roll 2D6 + ${statForSkill || '—'} DM ${trained ? '+ skill ' + level : '(unskilled −3)'}">
      <span class="tas-skill-name">${escapeHTML(displayName)}</span>${lvlBadge}
    </button>`;
}

// Build the full MGT2e skill tree, overlaying the character's trained levels.
function tasSkillsGrid() {
  const idx = tasSkillIndex();
  const core = SKILLS_DATA.core || [];
  const specs = SKILLS_DATA.speciality || {};
  // Combine: every core skill + every skill that has specialities, alphabetically.
  const allBase = Array.from(new Set([...core, ...Object.keys(specs)])).sort((a, b) => a.localeCompare(b));
  // Each base skill (and its specialties) is wrapped in a group block so the CSS
  // multi-column layout keeps a parent and its sub-skills together — specialties
  // always render directly under their main skill rather than scattering across
  // the column flow.
  const groups = [];
  allBase.forEach(name => {
    const stat = TAS_SKILL_STAT[name] || 'INT';
    if (specs[name]) {
      // Parent line (level 0 if any specialty trained or parent itself trained), then specialties.
      const parentLvl = idx.base[name];
      let block = tasSkillCell(name, name, parentLvl != null ? parentLvl : (idx.spec[name] ? 0 : null), stat, false);
      specs[name].forEach(sp => {
        const lvl = idx.spec[name] ? idx.spec[name][sp] : undefined;
        block += tasSkillCell(`${name} (${sp})`, `${name} (${sp})`, (lvl != null ? lvl : null), stat, true);
      });
      groups.push(`<div class="tas-skill-group">${block}</div>`);
    } else {
      groups.push(`<div class="tas-skill-group">${tasSkillCell(name, name, (idx.base[name] != null ? idx.base[name] : null), stat, false)}</div>`);
    }
  });
  const total = (character.skills || []).reduce((sum, s) => sum + (s.level || 0), 0);
  return { html: groups.join(''), total };
}

// Lore-appropriate banner text for the TAS form header, keyed by society then species.
function tasFormBanner() {
  const soc = character.society_id || '';
  const sp  = character.species_id  || '';
  if (soc === 'zhodani_consulate'  || sp.startsWith('zhodani'))  return ['ZHODANI CONSULATE',         'CITIZEN DOSSIER',            'FORM ZCONS-7 · PRITHYIR'];
  if (soc === 'aslan_hierate'      || sp.includes('aslan'))      return ['ASLAN HIERATE',              'PRIDE REGISTRY',             'FTEIRLE AOKHALTE · SEALED'];
  if (soc === 'two_thousand_worlds'|| sp.includes('kkree'))      return ['TWO THOUSAND WORLDS',        'HERD MANIFEST',              'KTEIRLE-FORM 1 · SEALED'];
  if (soc === 'vargr_extents'      || sp.includes('vargr'))      return ['VARGR EXTENTS',              'PACK CHARTER',               'CORSAIR REGISTRY · AEKHU'];
  if (soc === 'solomani_confederation' || sp === 'confederation_human' || sp === 'solomani') return ['SOLOMANI CONFEDERATION', 'GENETIC RECORD', 'FORM SOL-GR1 · RACIAL REGISTRY'];
  if (soc === 'droyne_oytrip'      || sp === 'droyne')           return ['DROYNE OYTRIP',              'CASTE CLASSIFICATION',       'FORM OY-7 · SPORT RESTRICTED'];
  if (soc === 'hiver_federation'   || sp === 'hiver')            return ['HIVER FEDERATION',           'NEST COLLECTIVE PROFILE',    'FORM HF-NEST · MANIPULATOR ONLY'];
  if (sp === 'dolphin' || sp === 'orca') return ['CETACEAN UPLIFT AUTHORITY',   'CITIZENSHIP RECORD',         'FORM CUA-3 · OCEAN TERRITORY'];
  // default — Third Imperium / mixed / unknown
  return ['TRAVELLERS\' AID SOCIETY',                            '— IMPERIAL TRAVEL AUTHORITY —', 'FORM TAS-001 · CONFIDENTIAL'];
}

// Render the interactive TAS character sheet.
function renderTASSheet() {
  const ps = tasPlay();
  const stats = character.characteristics;
  const species = SPECIES.find(s => s.id === character.species_id) || { name: character.species_id || '—' };
  const socLabel = socLabelForChar(character) || 'SOC';
  const dossier = (character.name || 'TRAVELLER').toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6).padEnd(4, '0').slice(0, 6);
  const initial = (character.name || 'F').trim().charAt(0).toUpperCase() || 'F';
  const [bannerLeft, bannerCenter, bannerRight] = tasFormBanner();
  const portrait = ps.portrait || null;

  // Characteristics (6 + PSI if any)
  const statList = ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC'].filter(s => s !== 'SOC' || socLabelForChar(character) !== null);
  if (character.psi > 0) statList.push('PSI');
  if (character.reputation > 0) statList.push('REP');
  const statNames = { STR:'Strength', DEX:'Dexterity', END:'Endurance', INT:'Intellect', EDU:'Education', SOC:'Social Standing', PSI:'Psionics', REP:'Reputation' };
  const statCards = statList.map(stat => {
    const val = tasStatVal(stat);
    const dm = charDM(val);
    const dmgd = (ps.dmg[stat] || 0) > 0;
    const label = stat === 'SOC' ? socLabel : (stat === 'PSI' ? 'PSI' : stat);
    return `
      <div class="tas-stat ${dmgd ? 'damaged' : ''}">
        <div class="tas-stat-label">${label}</div>
        <div class="tas-stat-sub">${statNames[stat] || ''}</div>
        <button class="tas-stat-val" data-roll-stat="${stat}" title="Click to roll 2D6 ${formatDM(dm)}">${val}</button>
        <div class="tas-stat-mod">Mod ${formatDM(dm)}</div>
        <div class="tas-stat-adj">
          <button data-stat-adj="${stat}" data-delta="-1" title="−1">–</button>
          <span>·</span>
          <button data-stat-adj="${stat}" data-delta="1" title="+1">+</button>
        </div>
      </div>`;
  }).join('');

  // Wielded weapons
  const wieldedHTML = ps.wielded.length
    ? ps.wielded.map((w, i) => `<div class="tas-wielded-item">${escapeHTML(w)} <button class="tas-x" data-unwield="${i}">×</button></div>`).join('')
    : `<p class="tas-empty">No weapons.</p>`;

  // Wound status
  const physDmg = (ps.dmg.STR || 0) + (ps.dmg.DEX || 0) + (ps.dmg.END || 0);
  const woundClass = physDmg === 0 ? 'ok' : (tasStatVal('STR') === 0 || tasStatVal('DEX') === 0 || tasStatVal('END') === 0 ? 'serious' : 'hurt');
  const woundLabel = physDmg === 0 ? 'UNWOUNDED' : (woundClass === 'serious' ? 'SERIOUSLY WOUNDED' : 'WOUNDED');
  const condChips = ps.conditions.length
    ? ps.conditions.map((c, i) => `<span class="tas-cond">${escapeHTML(c)} <button class="tas-x" data-cond-rm="${i}">×</button></span>`).join('')
    : `<span class="tas-empty">No active conditions</span>`;

  // Skills grid
  const skills = tasSkillsGrid();

  // Tabs
  const tab = uiState.sheetTab || 'combat';
  const tabBtn = (id, label) => `<button class="tas-tab ${tab === id ? 'active' : ''}" data-sheet-tab="${id}">${label}</button>`;

  return `
  <div class="tas-sheet">
    <div class="tas-form-top">
      <span>${escapeHTML(bannerLeft)}</span>
      <span>${escapeHTML(bannerCenter)}</span>
      <span>${escapeHTML(bannerRight)}</span>
    </div>

    <div class="tas-identity">
      <label class="tas-portrait" title="Click to upload a character portrait" style="cursor:pointer">
        ${portrait
          ? `<img src="${portrait}" alt="portrait" class="tas-portrait-img" />`
          : `<span class="tas-portrait-initial">${escapeHTML(initial)}</span><span class="tas-portrait-hint">UPLOAD</span>`}
        <input type="file" id="tas-portrait-input" accept="image/*" style="display:none" />
      </label>
      <div class="tas-id-fields">
        <input class="tas-name" id="tas-name" value="${escapeAttr(character.name || '')}" placeholder="UNNAMED TRAVELLER" />
        <div class="tas-id-row">
          <div class="tas-field"><label>RACE / SPECIES</label><div>${escapeHTML(species.name)}</div></div>
          <div class="tas-field"><label>AGE (YEARS)</label><div>${character.age ?? '—'}</div></div>
          <div class="tas-field"><label>HOMEWORLD</label><div>${escapeHTML(character.homeworld || '—')}</div></div>
        </div>
        <div class="tas-dossier">DOSSIER № <strong>${escapeHTML(dossier)}</strong></div>
      </div>
    </div><!-- /tas-identity -->

    <div class="tas-grid-2">
      <div class="tas-card">
        <div class="tas-card-head"><span>⚡ CHARACTERISTICS</span><em>Click a value to roll 2D6 + that DM</em></div>
        <div class="tas-stats">${statCards}</div>
      </div>
      <div class="tas-card">
        <div class="tas-card-head"><span>⚔ WIELDED</span><em>Add weapons in the Combat tab</em></div>
        <div class="tas-wielded">${wieldedHTML}</div>
      </div>
    </div>

    <div class="tas-card">
      <div class="tas-card-head"><span>✚ STATUS &amp; CONDITIONS</span><em>Wound status (derived) · active conditions</em></div>
      <div class="tas-status">
        <span class="tas-wound tas-wound-${woundClass}">${woundLabel}</span>
        <button class="tas-btn-dmg" id="tas-take-damage">⚠ TAKE DAMAGE</button>
        <button class="tas-btn-heal" id="tas-heal">HEAL ALL</button>
        <button class="tas-btn-cond" id="tas-add-cond">+ Add condition</button>
        <span class="tas-conds">${condChips}</span>
      </div>
    </div>

    <div class="tas-card">
      <div class="tas-card-head"><span>✦ SPECIES</span><em>${escapeHTML(species.name)}</em></div>
      <div class="tas-species">
        <span class="tas-species-tag">${escapeHTML(species.name)}</span>
        ${(character.traits && character.traits.length)
          ? character.traits.map(t => `<span class="tas-trait" title="${escapeAttr(t.description || '')}">${escapeHTML(t.name)}</span>`).join('')
          : '<span class="tas-empty">No alien traits</span>'}
      </div>
    </div>

    <div class="tas-card">
      <div class="tas-card-head"><span>📖 SKILLS</span><em>Total levels: ${skills.total} · click a skill to roll</em></div>
      <div class="tas-skills">${skills.html}</div>
    </div>

    <div class="tas-tabs">
      ${tabBtn('combat','⚔ Combat')}
      ${tabBtn('gear','🎒 Gear')}
      ${tabBtn('holdings','🏦 Holdings')}
      ${tabBtn('people','👥 People')}
      ${tabBtn('psionics','✦ Psionics')}
      ${tabBtn('notes','📝 Notes')}
    </div>
    <div class="tas-tab-body">${renderTASTab(tab)}</div>

    <div class="tas-foot">
      <span>Chargen complete · Mongoose Traveller 2.0 layout</span>
      <button class="tas-btn-fullscreen" id="tas-open-fullscreen" title="Open sheet in its own window">⛶ FULL SCREEN</button>
      <span class="tas-foot-brand">TRAVELLER</span>
    </div>
  </div>`;
}

// Render the active lower tab.
function renderTASTab(tab) {
  const ps = tasPlay();
  if (tab === 'combat') {
    const arm = (character.equipment || []).filter(e => e.protection != null);
    const armHTML = arm.length
      ? arm.map(e => `<div class="tas-line"><span>${escapeHTML(e.name)}</span><span class="tas-tag">Protection +${e.protection}</span></div>`).join('')
      : `<p class="tas-empty">No armour recorded.</p>`;
    const wHTML = ps.weapons.length
      ? ps.weapons.map((w, i) => `<div class="tas-line">
          <button class="tas-weapon-roll" data-weapon-atk="${i}" title="Roll attack (2D6 + relevant skill DM — pick your skill above)">${escapeHTML(w.name)}</button>
          <span class="tas-tag">${escapeHTML(w.dmg || '—')}</span>
          ${w.range ? `<span class="tas-tag ghost">${escapeHTML(w.range)}</span>` : ''}
          <button class="tas-wield-btn" data-wield="${i}" title="Hold this weapon">✋</button>
          <button class="tas-x" data-weapon-rm="${i}">×</button>
        </div>`).join('')
      : `<p class="tas-empty">No weapons recorded yet.</p>`;
    return `
      <div class="tas-sub">
        <div class="tas-sub-head">🛡 ARMOUR</div>
        ${armHTML}
      </div>
      <div class="tas-sub">
        <div class="tas-sub-head">💥 WEAPONS</div>
        ${wHTML}
        <div class="tas-add-row">
          <input id="tas-w-name" placeholder="Weapon name" />
          <input id="tas-w-dmg" placeholder="Damage e.g. 3D" class="narrow" />
          <input id="tas-w-range" placeholder="Range" class="narrow" />
          <button class="tas-btn-add" id="tas-w-add">Add</button>
        </div>
      </div>`;
  }
  if (tab === 'gear') {
    const gear = (character.equipment || []).filter(e => e.protection == null);
    return gear.length
      ? `<div class="tas-list">${gear.map(e => `<div class="tas-line"><span>${escapeHTML(e.name)}</span>${e.notes ? `<span class="tas-note">${escapeHTML(e.notes)}</span>` : ''}</div>`).join('')}</div>`
      : `<p class="tas-empty">No gear recorded.</p>`;
  }
  if (tab === 'holdings') {
    const benefits = [];
    benefits.push(`<div class="tas-line"><span>Credits</span><span class="tas-tag">Cr${(character.credits || 0).toLocaleString()}</span></div>`);
    if (character.ship_shares) benefits.push(`<div class="tas-line"><span>Ship Shares</span><span class="tas-tag">${character.ship_shares}</span></div>`);
    if (character.pension_per_year) benefits.push(`<div class="tas-line"><span>Pension</span><span class="tas-tag">Cr${character.pension_per_year.toLocaleString()}/yr</span></div>`);
    if (character.medical_debt) benefits.push(`<div class="tas-line"><span>Medical Debt</span><span class="tas-tag danger">Cr${character.medical_debt.toLocaleString()}</span></div>`);
    (character.benefits || []).forEach(b => benefits.push(`<div class="tas-line"><span>${escapeHTML(typeof b === 'string' ? b : (b.name || JSON.stringify(b)))}</span></div>`));
    return `<div class="tas-list">${benefits.join('')}</div>`;
  }
  if (tab === 'people') {
    const assoc = (character.associates || []).filter(a => a.kind !== 'wife');
    if (!assoc.length) return `<p class="tas-empty">No contacts, allies, rivals or enemies.</p>`;
    const order = [['contact','Contacts'],['ally','Allies'],['rival','Rivals'],['enemy','Enemies']];
    return order.map(([k, title]) => {
      const items = assoc.filter(a => a.kind === k);
      if (!items.length) return '';
      return `<div class="tas-sub"><div class="tas-sub-head tas-assoc-${k}">${title}</div>
        ${items.map(a => `<div class="tas-line"><span>${escapeHTML(a.description || '(unnamed)')}</span></div>`).join('')}</div>`;
    }).join('');
  }
  if (tab === 'psionics') {
    if (!character.psi_tested) return `<p class="tas-empty">Not psionically tested.</p>`;
    if (character.psi <= 0) return `<p class="tas-empty">Tested — no psionic potential (PSI 0).</p>`;
    const talents = (character.skills || []).filter(s => ['Telepathy','Clairvoyance','Telekinesis','Awareness','Teleportation'].includes(s.name));
    return `<div class="tas-line"><span><strong>PSI ${character.psi}</strong></span><span class="tas-tag">DM ${formatDM(charDM(character.psi))}</span></div>
      ${talents.length ? talents.map(t => `<button class="tas-skill trained inline" data-skill-roll="${escapeAttr(t.name)}" data-skill-level="${t.level}" data-skill-stat=""><span class="tas-skill-name">${escapeHTML(t.name)}</span><span class="tas-skill-lvl">${t.level}</span></button>`).join('') : '<p class="tas-empty">No talents trained.</p>'}`;
  }
  if (tab === 'notes') {
    return `<textarea id="tas-notes" class="tas-notes" placeholder="Free notes — quirks, goals, contacts, gear details…">${escapeHTML(ps.notes || '')}</textarea>`;
  }
  return '';
}

// Open the sheet in a standalone window with a theme/colour switcher for printing.
function openTASFullscreen() {
  const cssLinks = Array.from(document.styleSheets)
    .map(s => { try { return s.href; } catch(e) { return null; } })
    .filter(h => h && !h.includes('fonts.googleapis'))
    .map(h => `<link rel="stylesheet" href="${h}" />`)
    .join('\n');
  const sheetHTML = document.getElementById('tas-sheet-mount')?.innerHTML || '';
  const charName = (character.name || 'Traveller');
  const w = window.open('', '_blank', 'width=920,height=960,scrollbars=yes,resizable=yes');
  if (!w) return;
  w.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>${charName} — Character Sheet</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=VT323&family=Cormorant+Garamond:wght@400;600;700&display=swap" />
  ${cssLinks}
  <style>
    /* ── base layout ── */
    body { margin: 0; padding: 0 16px 24px; background: var(--bg-deep, #0a0806); }
    .tas-sheet { max-width: 860px; margin: 0 auto; }
    .tas-btn-fullscreen { display: none !important; }
    button, input { pointer-events: none; opacity: 0.7; }
    label.tas-portrait { pointer-events: none; }

    /* ── colour switcher toolbar ── */
    #sheet-toolbar {
      max-width: 860px; margin: 0 auto; padding: 8px 2px;
      display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
      font-family: 'JetBrains Mono', monospace; font-size: 11px;
    }
    #sheet-toolbar span { color: #9a8064; letter-spacing: 1px; }
    .tb-btn {
      padding: 4px 12px; border-radius: 4px; cursor: pointer; border: 1px solid;
      font-family: inherit; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
      transition: opacity 0.15s;
    }
    .tb-btn:hover { opacity: 0.85; }
    .tb-amber  { background:#120e0a; border-color:#6b4a20; color:#ffb347; }
    .tb-green  { background:#0a120a; border-color:#3fa85c; color:#6fff8f; }
    .tb-print  { background:#ffffff; border-color:#aaaaaa; color:#111111; }
    .tb-print-dark { background:#111111; border-color:#444444; color:#eeeeee; }
    .tb-active { outline: 2px solid currentColor; outline-offset: 2px; }
    .tb-sep { flex: 1; }
    .tb-print-btn {
      padding: 4px 14px; border-radius: 4px; cursor: pointer;
      border: 1px solid #c0392b; background: rgba(192,57,43,0.15); color: #e0503e;
      font-family: inherit; font-size: 11px; font-weight: 700;
    }
    .tb-print-btn:hover { background: rgba(192,57,43,0.3); }

    /* ── PRINT mode: black on white ── */
    body.theme-print {
      --bg-deep: #ffffff; --bg-panel: #f8f8f8; --bg-panel-alt: #eeeeee;
      --border: #cccccc; --border-glow: #999999;
      --amber: #111111; --amber-bright: #000000; --amber-dim: #444444;
      --amber-deep: #333333; --cream: #111111; --muted: #555555;
      --danger: #000000; --danger-bg: #f0f0f0;
      --success: #111111; --tint-rgb: 0,0,0;
      background: #ffffff;
    }
    body.theme-print .tas-form-top { background: #111111; color: #ffffff; }
    body.theme-print .tas-stat-val { text-shadow: none; }
    body.theme-print .tas-skill.trained { background: #eeeeee; }

    /* ── PRINT DARK: white on black ── */
    body.theme-print-dark {
      --bg-deep: #000000; --bg-panel: #0d0d0d; --bg-panel-alt: #1a1a1a;
      --border: #333333; --border-glow: #555555;
      --amber: #eeeeee; --amber-bright: #ffffff; --amber-dim: #aaaaaa;
      --amber-deep: #666666; --cream: #dddddd; --muted: #777777;
      --danger: #cccccc; --danger-bg: rgba(200,200,200,0.1);
      --success: #aaaaaa; --tint-rgb: 220,220,220;
      background: #000000;
    }
    body.theme-print-dark .tas-form-top { background: #222222; }
    body.theme-print-dark .tas-stat-val { text-shadow: none; }

    /* ── suppress toolbar when printing ── */
    @media print {
      #sheet-toolbar { display: none !important; }
      body { padding: 0; }
      .tas-sheet { box-shadow: none !important; border: none !important; }
    }
  </style>
</head>
<body>
  <div id="sheet-toolbar">
    <span>COLOUR:</span>
    <button class="tb-btn tb-amber tb-active" data-theme="">AMBER</button>
    <button class="tb-btn tb-green"           data-theme="gm-active">GREEN</button>
    <button class="tb-btn tb-print"           data-theme="theme-print">B &amp;W PRINT</button>
    <button class="tb-btn tb-print-dark"      data-theme="theme-print-dark">DARK PRINT</button>
    <span class="tb-sep"></span>
    <button class="tb-print-btn" onclick="window.print()">⎙ PRINT</button>
  </div>
  ${sheetHTML}
  <script>
    document.querySelectorAll('[data-theme]').forEach(btn => {
      btn.addEventListener('click', () => {
        const themes = ['gm-active','theme-print','theme-print-dark'];
        themes.forEach(t => document.body.classList.remove(t));
        if (btn.dataset.theme) document.body.classList.add(btn.dataset.theme);
        document.querySelectorAll('.tb-btn').forEach(b => b.classList.remove('tb-active'));
        btn.classList.add('tb-active');
      });
    });
  <\/script>
</body>
</html>`);
  w.document.close();
}

// Wire up all interactive controls on the sheet.
function wireTASSheet() {
  // Portrait upload
  const portraitInput = document.getElementById('tas-portrait-input');
  if (portraitInput) {
    portraitInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        tasPlay().portrait = ev.target.result;
        refreshTASSheet();
      };
      reader.readAsDataURL(file);
    });
  }

  // Fullscreen button
  const fsBtn = document.getElementById('tas-open-fullscreen');
  if (fsBtn) fsBtn.addEventListener('click', openTASFullscreen);

  // Name edit
  const nameEl = document.getElementById('tas-name');
  if (nameEl) nameEl.addEventListener('change', () => { character.name = nameEl.value.trim(); refreshTASSheet(); });

  // Stat roll
  document.querySelectorAll('[data-roll-stat]').forEach(b =>
    b.addEventListener('click', () => tasRollStat(b.dataset.rollStat)));

  // Stat +/- adjust
  document.querySelectorAll('[data-stat-adj]').forEach(b =>
    b.addEventListener('click', () => {
      const stat = b.dataset.statAdj, delta = parseInt(b.dataset.delta, 10);
      if (stat === 'PSI') { character.psi = Math.max(0, (character.psi || 0) + delta); }
      else { character.characteristics[stat] = Math.max(0, (character.characteristics[stat] || 0) + delta); }
      refreshTASSheet();
    }));

  // Skill roll
  document.querySelectorAll('[data-skill-roll]').forEach(b =>
    b.addEventListener('click', () => {
      const lvlStr = b.dataset.skillLevel;
      const lvl = lvlStr === '' ? null : parseInt(lvlStr, 10);
      tasRollSkill(b.dataset.skillRoll, lvl, b.dataset.skillStat || null);
    }));

  // Take damage
  const dmgBtn = document.getElementById('tas-take-damage');
  if (dmgBtn) dmgBtn.addEventListener('click', () => {
    const amt = parseInt(prompt('Damage taken (applied to END, then STR, then DEX per MGT2e):', '1'), 10);
    if (!amt || amt < 1) return;
    const ps = tasPlay();
    let remaining = amt;
    ['END', 'STR', 'DEX'].forEach(stat => {
      if (remaining <= 0) return;
      const cur = tasStatVal(stat);
      const take = Math.min(cur, remaining);
      ps.dmg[stat] = (ps.dmg[stat] || 0) + take;
      remaining -= take;
    });
    refreshTASSheet();
  });

  // Heal all
  const healBtn = document.getElementById('tas-heal');
  if (healBtn) healBtn.addEventListener('click', () => { tasPlay().dmg = {}; refreshTASSheet(); });

  // Add condition
  const condBtn = document.getElementById('tas-add-cond');
  if (condBtn) condBtn.addEventListener('click', () => {
    const c = prompt('Condition (e.g. Stunned, Prone, Diseased):', '');
    if (c && c.trim()) { tasPlay().conditions.push(c.trim()); refreshTASSheet(); }
  });
  document.querySelectorAll('[data-cond-rm]').forEach(b =>
    b.addEventListener('click', () => { tasPlay().conditions.splice(parseInt(b.dataset.condRm, 10), 1); refreshTASSheet(); }));

  // Tabs
  document.querySelectorAll('[data-sheet-tab]').forEach(b =>
    b.addEventListener('click', () => { uiState.sheetTab = b.dataset.sheetTab; refreshTASSheet(); }));

  // Weapons add / remove / wield
  const wAdd = document.getElementById('tas-w-add');
  if (wAdd) wAdd.addEventListener('click', () => {
    const name = (document.getElementById('tas-w-name').value || '').trim();
    if (!name) return;
    tasPlay().weapons.push({
      name,
      dmg: (document.getElementById('tas-w-dmg').value || '').trim(),
      range: (document.getElementById('tas-w-range').value || '').trim(),
    });
    refreshTASSheet();
  });
  document.querySelectorAll('[data-weapon-rm]').forEach(b =>
    b.addEventListener('click', () => { tasPlay().weapons.splice(parseInt(b.dataset.weaponRm, 10), 1); refreshTASSheet(); }));
  document.querySelectorAll('[data-wield]').forEach(b =>
    b.addEventListener('click', () => { const w = tasPlay().weapons[parseInt(b.dataset.wield, 10)]; if (w) { tasPlay().wielded.push(w.name); refreshTASSheet(); } }));
  document.querySelectorAll('[data-unwield]').forEach(b =>
    b.addEventListener('click', () => { tasPlay().wielded.splice(parseInt(b.dataset.unwield, 10), 1); refreshTASSheet(); }));
  document.querySelectorAll('[data-weapon-atk]').forEach(b =>
    b.addEventListener('click', () => {
      const w = tasPlay().weapons[parseInt(b.dataset.weaponAtk, 10)];
      const r = tasRoll2D(0);
      tasToast(`<strong>${escapeHTML(w.name)}</strong> attack · 2D6 [${r.d1}+${r.d2}] = <span class="tas-toast-total">${r.total}</span> (add your skill + DEX DM)${w.dmg ? ` · dmg ${escapeHTML(w.dmg)}` : ''}`, 'roll');
    }));

  // Notes
  const notesEl = document.getElementById('tas-notes');
  if (notesEl) notesEl.addEventListener('change', () => { tasPlay().notes = notesEl.value; saveCharacter(); });
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
  // Cascade-specialty cleanup (button + picker) is available on the done screen.
  wireCascadeCleanup();

  // ── Robot done phase wiring ──
  const btnRobotFoundry = document.getElementById('btn-export-robot-foundry');
  if (btnRobotFoundry) {
    btnRobotFoundry.addEventListener('click', () => {
      try {
        const cfg = robotNormalize(character.robot_config || {});
        const actor = createRobotFoundryExport(cfg);
        const payload = JSON.stringify(actor, null, 2);
        const blob = new Blob([payload], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${(cfg.name||'robot').toLowerCase().replace(/[^a-z0-9]+/g,'-')}-foundry.json`;
        a.click();
        URL.revokeObjectURL(url);
      } catch(e) { alert('Export failed: ' + e.message); }
    });
  }
  const btnBackRobot = document.getElementById('btn-back-to-robot-build');
  if (btnBackRobot) btnBackRobot.addEventListener('click', () => {
    character.phase = 'robot_build';
    uiState.robotTab = 'finalize';
    saveCharacter();
    renderAll();
  });

  // ── Normal done phase wiring ──
  const btnExport = document.getElementById('btn-export-prominent');
  if (btnExport) btnExport.addEventListener('click', exportCharacter);

  // Interactive character sheet (replaces the old PDF export).
  if (document.getElementById('tas-sheet-mount')) wireTASSheet();

  const btnFoundry = document.getElementById('btn-export-foundry');
  if (btnFoundry) btnFoundry.addEventListener('click', exportFoundry);
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
  document.getElementById('btn-new-char').addEventListener('click', async () => {
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
    try {
      await freshCharacter();
      renderAll();
    } catch (e) {
      alert('Failed to create new character: ' + e.message);
    }
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

async function exportFoundry() {
  const btn = document.getElementById('btn-export-foundry');
  if (btn) { btn.textContent = 'GENERATING…'; btn.disabled = true; }
  try {
    const res = await fetch('/api/character/export-foundry', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ character }),
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(character.name || 'traveller').replace(/\s+/g, '_')}_foundry.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (e) {
    alert('Foundry export failed: ' + e.message);
  } finally {
    if (btn) { btn.textContent = '⬇ EXPORT TO FOUNDRY'; btn.disabled = false; }
  }
}

async function importCharacter(file) {
  const text = await file.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (e) {
    alert('Invalid character JSON: ' + e.message);
    return;
  }
  try {
    // Detect a FoundryVTT MGT2e actor (vs a native TravllerCC export). Handle the
    // wrapper shapes Foundry sometimes uses: a bare actor, [actor], {actor:…}.
    let actor = data;
    if (Array.isArray(actor)) actor = actor[0];
    if (actor && typeof actor === 'object' && actor.actor && typeof actor.actor === 'object') actor = actor.actor;
    const isFoundry = !!(actor && typeof actor === 'object' && actor.type === 'traveller' && actor.system);

    if (isFoundry) {
      const res = await fetch('/api/character/import-foundry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ actor }),
      });
      if (!res.ok) {
        const body = await res.text().catch(() => '');
        let detail; try { detail = JSON.parse(body).detail; } catch { detail = body; }
        throw new Error(detail || `Foundry import failed (HTTP ${res.status})`);
      }
      const resp = await res.json();
      character = resp.character;
      if (resp.lossless === false) {
        alert('Imported from a Foundry actor. Stats, skills, gear and contacts were '
            + 'restored, but career history and the lifepath log are not stored in a '
            + 'Foundry export — review the sheet before play.');
      }
    } else {
      character = data;
    }
    // Reset transient navigation/selection state so the imported character
    // renders cleanly from its OWN phase rather than inheriting the current
    // view. In particular a finished (phase "done") character lands on the
    // "Your Traveller Is Ready" screen — where it can be pulled back in and
    // cleaned up (e.g. cascade-skill specialties) — and a mid-creation save
    // resumes at the correct step via the career sub-phase inference.
    uiState.subPhase = null;
    uiState.lastRoll = null;
    uiState.lastAdvanceRoll = null;
    uiState.cascadeCleanupMode = false;
    uiState.cascadeCleanupChoices = {};
    uiState.selectedMusterIndex = null;
    uiState.selectedCareer = null;
    uiState.selectedAssignment = null;
    uiState.pendingCareerSpecialty = null;
    uiState.pendingAdvancementSkill = false;
    saveCharacter();
    renderAll();
  } catch (e) {
    alert('Import failed: ' + (e.message || e));
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

  try {
    const bgPkgRes = await fetch('/api/tables/background-packages');
    if (bgPkgRes.ok) BG_PACKAGES = await bgPkgRes.json();
  } catch (e) { /* non-fatal */ }

  try {
    const cpRes = await fetch('/api/tables/career-packages');
    if (cpRes.ok) CAREER_PACKAGES = await cpRes.json();
  } catch (e) { /* non-fatal */ }

  // Apply saved theme before first paint
  document.body.classList.toggle('theme-light', uiState.theme === 'light');
  document.body.classList.toggle('theme-mono',  uiState.theme === 'mono');
  // Apply saved desc-hide state before first paint
  if (uiState.hideDesc) document.body.classList.add('hide-card-desc');

  // Mobile tab bar wiring
  wireMobileTabs();

  renderAll();

  document.getElementById('btn-export').addEventListener('click', exportCharacter);
  document.getElementById('import-file').addEventListener('change', (e) => {
    if (e.target.files[0]) importCharacter(e.target.files[0]);
  });

  document.getElementById('btn-reset').addEventListener('click', async () => {
    if (!confirm('Start a new character? This will wipe the current character and log.')) return;
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* ignore */ }
    try {
      await freshCharacter();
      renderAll();
    } catch (e) {
      alert('Failed to create new character: ' + e.message);
    }
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

  // Description toggle (¶ button) — hides .card-desc on all picker cards
  const btnDesc = document.getElementById('btn-desc-toggle');
  if (btnDesc) {
    const applyDesc = () => {
      document.body.classList.toggle('hide-card-desc', !!uiState.hideDesc);
      btnDesc.classList.toggle('desc-active', !!uiState.hideDesc);
      btnDesc.title = uiState.hideDesc ? 'Show card descriptions' : 'Hide card descriptions';
    };
    applyDesc();
    btnDesc.addEventListener('click', () => {
      uiState.hideDesc = !uiState.hideDesc;
      try { localStorage.setItem('traveller_hide_desc', uiState.hideDesc ? '1' : '0'); } catch (e) { /* ignore */ }
      applyDesc();
    });
  }

  // Theme cycle: dark → light → mono → dark
  const btnTheme = document.getElementById('btn-theme-toggle');
  if (btnTheme) {
    const THEME_CYCLE = ['dark', 'light', 'mono'];
    const THEME_ICONS = { dark: '◐', light: '◑', mono: '◉' };
    const THEME_NEXT_LABEL = {
      dark:  'Switch to green-terminal theme',
      light: 'Switch to monochrome theme',
      mono:  'Switch to amber CRT theme',
    };
    const applyTheme = () => {
      const t = uiState.theme;
      document.body.classList.toggle('theme-light', t === 'light');
      document.body.classList.toggle('theme-mono',  t === 'mono');
      btnTheme.textContent = THEME_ICONS[t] || '◐';
      btnTheme.title = THEME_NEXT_LABEL[t] || 'Switch theme';
    };
    applyTheme();
    btnTheme.addEventListener('click', () => {
      const idx = THEME_CYCLE.indexOf(uiState.theme);
      uiState.theme = THEME_CYCLE[(idx + 1) % THEME_CYCLE.length];
      try { localStorage.setItem('theme', uiState.theme); } catch (e) { /* ignore */ }
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

  // Save/Load slots modal
  const savesBtn   = document.getElementById('btn-saves');
  const savesModal = document.getElementById('saves-modal');
  const savesClose = document.getElementById('btn-close-saves');
  if (savesBtn && savesModal) {
    savesBtn.addEventListener('click', () => {
      renderSavesModal();
      savesModal.hidden = false;
    });
  }
  if (savesClose && savesModal) {
    savesClose.addEventListener('click', () => { savesModal.hidden = true; });
    savesModal.addEventListener('click', (e) => {
      if (e.target === savesModal) savesModal.hidden = true;
    });
  }
}

bootstrap();
