FUNCTION_BLOCK FB_X
VAR
    sValve             : tValve
        (
         bOpen         := True,
         iMax          := 10,
         rGain         := 1.5
         );  // valve
    sb                 : Bool;
    sName              : String(80) := 'x';
{attribute 'a'} sOther : tOther :=
        (
         iA            := 1,
         iB            := 2
         );
    saArr              : Array[1..2] Of Int := [1, 2];
END_VAR
sb                     := True;
