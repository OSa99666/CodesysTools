TYPE tA :
STRUCT //{attribute 'noprefix'}
    Alpha : INT;
    Beta : BOOL;
END_STRUCT
END_TYPE
TYPE tB :
STRUCT
    Gamma : INT;
END_STRUCT
END_TYPE
FUNCTION_BLOCK FB_X
VAR (* {attribute 'noprefix'} *)
    Free : INT;
END_VAR
VAR
    Checked : INT;
END_VAR
END_FUNCTION_BLOCK
