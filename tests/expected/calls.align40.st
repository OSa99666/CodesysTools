PROGRAM Main
VAR
    sTimer                             : TON;
    sbStart                            : Bool;
    sbDone                             : Bool;
    stElapsed                          : Time;
    srX                                : Real;
END_VAR
sbStart                                := True;
sTimer
    (
     IN                                := sbStart,
     PT                                := T#5S,  // time
     Q                                 => sbDone,
     ET                                => stElapsed
     );                                          // done
If sbStart Then
    aFb[1].Run
        (
         Execute                       := True
         );
    srX                                := Limit(0.0, srX, 10.0);
    F_Calc(srX);
End_If
srX                                    := a +
F(b := 1);
sTimer
    (
     // comment line
     IN                                := sbStart
     );
END_PROGRAM
