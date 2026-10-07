VAR_GLOBAL
    gbAlarm : BOOL;
    bAlarm2 : BOOL;
    iStart AT %IX0.0 : BOOL;
    ibStop AT %IX0.1 : BOOL;
    qbLamp AT %QX0.0 : BOOL;
END_VAR
VAR_GLOBAL CONSTANT
    gciMax : INT := 10;
    MAX_N : INT := 5;
END_VAR
FUNCTION_BLOCK fbMotor
VAR_INPUT
    ibReset : BOOL;
    nSpeed : INT;
    ixEnable, bRun : BOOL;
    iAxis : ST_Axis;
END_VAR
VAR_OUTPUT
    qrSpeed : REAL;
    qlrPos : LREAL;
END_VAR
VAR_IN_OUT
    iqData : ST_Data;
END_VAR
VAR
    sbReset : BOOL;
    tonDelay : TON;
    sTimer : TON;
    aBuf : ARRAY[1..10] OF REAL;
    srBuf2 : ARRAY[1..10] OF REAL;
    sudiCount : UDINT := 0;
    sString : STRING(80);
    ssName : STRING(80);
    sdtStamp : DT;
END_VAR
VAR CONSTANT
    ciLimit : INT := 3;
END_VAR
VAR_TEMP
    ttElapsed : TIME;
    tData : ST_Data;
END_VAR
END_FUNCTION_BLOCK
FUNCTION fcAdd : INT
VAR
    tiX : INT;
    siY : INT;
END_VAR
END_FUNCTION
TYPE ST_Data :
STRUCT
    bOk : BOOL;
    rVal : REAL;
    value : INT;
    Sub : ST_Sub;
END_STRUCT
END_TYPE
