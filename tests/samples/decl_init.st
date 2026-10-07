FUNCTION_BLOCK FB_X
VAR
    sValve:tValve(bOpen:=TRUE, iMax:=10, rGain := 1.5);   // valve
    sb : BOOL;
    sName : STRING(80) := 'x';
    {attribute 'a'} sOther : tOther := (iA:=1,iB:=2);
    saArr : ARRAY[1..2] OF INT := [1,2];
END_VAR
sb := TRUE;
