FUNCTION_BLOCK fb_Motor
VAR_INPUT
    bStart:BOOL;   // start command
        {attribute 'hide'}
    bInternalFlagLongName : BOOL:=FALSE; (* stop *)
  {attribute 'hide'}   nCnt:LINT;
END_VAR
var_output
x:lreal; // out
end_var
REGION Motor If control
if bStart then
iState:=1; // run
elsif bStop then
iCounterValue:=0;
else
   x:=-5;
end_if
END_REGION
for i:=1 to 10 do
aBuffer[i]:=i; // fill
end_for
END_FUNCTION_BLOCK
