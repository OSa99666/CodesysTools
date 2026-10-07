PROGRAM Main
VAR
    sTimer : TON;
    sbStart : BOOL;
    sbDone : BOOL;
    stElapsed : TIME;
    srX : REAL;
END_VAR
sbStart:=TRUE;
sTimer(IN:=sbStart, PT:=T#5S, // time
       Q=>sbDone, ET=>stElapsed);   // done
IF sbStart THEN
  aFb[1].Run(Execute := TRUE);
  srX := LIMIT(0.0, srX, 10.0);
  F_Calc(srX);
END_IF
srX := a +
  F(b := 1);
sTimer(
// comment line
IN:=sbStart);
END_PROGRAM
