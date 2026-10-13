//{attribute 'noprefix'}
{attribute 'pack_mode' := '1'}
TYPE tMbUnion :
UNION
    b   : tMbState;  //For Bit Access
    dw  : DWord;     //For DoubleWord Access
    w2  : Word;
    Raw : Int;
    foo : Int;
END_UNION
END_TYPE
