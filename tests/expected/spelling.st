// This valve is wrong, the wrod is spelled wrong
(* Valves and unhappy workers check the lines *)
FUNCTION_BLOCK FB_Valve
VAR
    sbOpen    : Bool;   // The valve colour: a PLC flag with a mispelling
    sbValveOk : Bool;   // valvs of London and tMbState and sValve
END_VAR
// sbOpen := TRUE;  commented out code is skipped
// See https://example.com/wrodd and file.txt for details
sbOpen        := True;  // Worke it, e.g. unworkers and valveed
(* Multi
   line commment
   second: chek the line *)
// {attribute 'noprefix'}
// arbeidsbord og ventilbord, løs og ære, feilstavet ventilbrod
END_FUNCTION_BLOCK
