TYPE tA :
STRUCT  //{attribute 'noprefix'}
    Alpha   : Int;
    Beta    : Bool;
END_STRUCT
END_TYPE
TYPE tB :
STRUCT
    Gamma   : Int;
END_STRUCT
END_TYPE
FUNCTION_BLOCK FB_X
VAR     (* {attribute 'noprefix'} *)
    Free    : Int;
END_VAR
VAR
    Checked : Int;
END_VAR
END_FUNCTION_BLOCK
