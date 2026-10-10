FUNCTION_BLOCK fb_Motor EXTENDS fb_Base
VAR_INPUT
    bStart             : Bool;                        // start command
    bStop              : Bool := False;               // stop
    nSpeedSetpoint     : Int;
END_VAR
VAR
    tonDelay           : TON;
    aBuffer            : Array[1..10] Of Real;
    sName              : String(80) := 'Motor $'A$'';
    iState             : Int;
    dtStart            : DT := DT#2024-01-01-12:30:00;
    pIn AT %IX0.1      : Bool;
END_VAR

(* main logic *)
If bStart And Not bStop Then
    iState             := 1;
ElsIf bStop Then
    iState             := 0;
Else
    x                  := -5 + y * (3 - z);
End_If

Case iState Of
    0:
        tonDelay
            (
             IN        := False,
             PT        := T#2S
             );
    1, 2: tonDelay(IN := True,
            PT         := T#5s);
        If tonDelay.Q Then
            iState     := E_State#Running;
        End_If
    -1:;
Else
    iState             := 0;
End_Case

For i := 1 To 10 By 1 Do
    aBuffer[i]         := Int_To_Real(i) * 1.5E3;
End_For
Repeat
    i                  := i + 1;
Until i > 5
End_Repeat;
END_FUNCTION_BLOCK

TYPE ST_Data :
STRUCT
    a                  : Int;                         // first
    longName           : LReal := 1.0;
END_STRUCT
END_TYPE

PROGRAM Main
VAR
    i                  : Int;                         // loop counter
    rTemperatureActual : Real := 20.5;                // measured
    bAlarm             : Bool;
END_VAR
i                      := 0;                          // reset
rTemperatureActual     := rTemperatureActual + 0.1;
bAlarm                 := rTemperatureActual > 80.0;  // high temp
THIS^.x                := 1;
END_PROGRAM
