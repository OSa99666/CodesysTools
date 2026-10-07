FUNCTION_BLOCK fb_Motor EXTENDS fb_Base
VAR_INPUT
bStart:BOOL;   // start command
  bStop : BOOL:=FALSE; (* stop *)
nSpeedSetpoint:INT;
END_VAR
var
tonDelay:TON;
aBuffer : ARRAY [1..10] OF REAL;
sName:STRING(80):='Motor $'A$'';
iState : INT;
dtStart:DT:=DT#2024-01-01-12:30:00;
pIn AT %IX0.1:BOOL;
end_var

(* main logic *)
if bStart and not bStop then
iState:=1;
elsif bStop then
iState := 0;
else
   x:=-5+y*(3-z);
end_if



case iState of
0:
tonDelay(IN:=FALSE,PT:=T#2S);
1,2:   tonDelay(IN:=TRUE,
PT:=T#5s);
IF tonDelay.Q THEN
iState:=E_State#Running;
END_IF
-1: ;
else
iState:=0;
end_case

FOR i:=1 TO 10 BY 1 DO
aBuffer[i]:=INT_TO_REAL(i)*1.5E3;
END_FOR
REPEAT
i:=i+1;
UNTIL i>5
END_REPEAT;
END_FUNCTION_BLOCK

TYPE ST_Data :
STRUCT
a:INT; // first
longName : LREAL := 1.0;
END_STRUCT
END_TYPE

PROGRAM Main
VAR
    i:INT; (* loop counter *)
    rTemperatureActual : REAL := 20.5; // measured
    bAlarm:BOOL;
END_VAR
i:=0; // reset
rTemperatureActual:=rTemperatureActual+0.1;
bAlarm := rTemperatureActual>80.0;   // high temp
THIS^.x:=1;
END_PROGRAM
