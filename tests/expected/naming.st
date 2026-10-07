VAR_GLOBAL
    gbAlarm          : Bool;
    bAlarm2          : Bool;
    iStart AT %IX0.0 : Bool;
    ibStop AT %IX0.1 : Bool;
    qbLamp AT %QX0.0 : Bool;
END_VAR
VAR_GLOBAL CONSTANT
    gciMax           : Int := 10;
    MAX_N            : Int := 5;
END_VAR
FUNCTION_BLOCK fbMotor
VAR_INPUT
    ibReset          : Bool;
    nSpeed           : Int;
    ixEnable, bRun   : Bool;
    iAxis            : ST_Axis;
END_VAR
VAR_OUTPUT
    qrSpeed          : Real;
    qlrPos           : LReal;
END_VAR
VAR_IN_OUT
    iqData           : ST_Data;
END_VAR
VAR
    sbReset          : Bool;
    tonDelay         : TON;
    sTimer           : TON;
    aBuf             : Array[1..10] Of Real;
    srBuf2           : Array[1..10] Of Real;
    sudiCount        : UDInt := 0;
    sString          : String(80);
    ssName           : String(80);
    sdtStamp         : DT;
END_VAR
VAR CONSTANT
    ciLimit          : Int := 3;
END_VAR
VAR_TEMP
    ttElapsed        : Time;
    tData            : ST_Data;
END_VAR
END_FUNCTION_BLOCK
FUNCTION fcAdd : Int
VAR
    tiX              : Int;
    siY              : Int;
END_VAR
END_FUNCTION
TYPE ST_Data :
STRUCT
    bOk              : Bool;
    rVal             : Real;
    value            : Int;
    Sub              : ST_Sub;
END_STRUCT
END_TYPE
