FUNCTION_BLOCK fb_Motor
VAR_INPUT
    bStart                               : Bool;           // start command
{attribute 'hide'} bInternalFlagLongName : Bool := False;  // stop
{attribute 'hide'} nCnt                  : LInt;
END_VAR
VAR_OUTPUT
    x                                    : LReal;          // out
END_VAR
REGION Motor If control
    If bStart Then
        iState                           := 1;             // run
    ElsIf bStop Then
        iCounterValue                    := 0;
    Else
        x                                := -5;
    End_If
END_REGION
For i := 1 To 10 Do
    aBuffer[i]                           := i;             // fill
End_For
END_FUNCTION_BLOCK
