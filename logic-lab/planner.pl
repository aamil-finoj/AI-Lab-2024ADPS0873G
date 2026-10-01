% planner.pl -- Prolog as an independent verifier for the warehouse plan
% Run:  swipl planner.pl     then query at the ?- prompt.

% ---- Task 6: facts describing the warehouse ---------------------------------
connected(a,b).
connected(b,a).
connected(b,c).
connected(c,b).

% can_move(X,Y) :- connected(X,Y).     i.e.  Connected(X,Y) -> CanMove(X,Y)
can_move(X,Y) :-
    connected(X,Y).

% ---- Task 7: checking a proposed plan ---------------------------------------
valid_move(X,Y) :-
    connected(X,Y).

% Extra: check a whole route, e.g.  ?- valid_route([a,b,c]).
valid_route([_]).
valid_route([X,Y|Rest]) :-
    valid_move(X,Y),
    valid_route([Y|Rest]).

% ---- Task 8: rule chaining --------------------------------------------------
wet_road.
slippery :-
    wet_road.
reduce_speed :-
    slippery.

% ---- Background example (penguin) -------------------------------------------
penguin(polly).
bird(X) :-
    penguin(X).
animal(X) :-
    bird(X).
