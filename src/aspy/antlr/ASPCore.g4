/* Based on the latest ASP-Core 2 standard.

For details see https://www.cambridge.org/core/journals/theory-and-practice-of-logic-programming/article/abs/aspcore2-input-language-format/292E52334010C1F62E4469ABCD66228E.
*/

grammar ASPCore;

/* parser rules */

program             :   statements? query? EOF ;

statements          :   statement+ ;

query               :   classical_literal QUERY_MARK ;

statement           :   CONS body? DOT
                    |   head (CONS body?)? DOT
                    |   WCONS body? DOT SQUARE_OPEN weight_at_level SQUARE_CLOSE
                    ;

head                :   disjunction
                    |   choice
                    ;

body                :   (naf_literal | NAF? aggregate) (COMMA body)? ;

disjunction         :   classical_literal (OR disjunction)? ;

choice              :   (term relop)? CURLY_OPEN choice_elements? CURLY_CLOSE (relop term)? ;

choice_elements     :   choice_element (SEMICOLON choice_elements)? ;

choice_element      :   classical_literal (COLON naf_literals?)? ;

aggregate           :   (term relop)? aggregate_function CURLY_OPEN aggregate_elements? CURLY_CLOSE (relop term)? ;

aggregate_elements  :   aggregate_element (SEMICOLON aggregate_elements)? ;

aggregate_element   :   terms COLON?
                    |   COLON naf_literals?
                    |   terms COLON naf_literals
                    ;

aggregate_function  :   COUNT
                    |   MAX
                    |   MIN
                    |   SUM
                    ;

weight_at_level     :   term (AT term)? (COMMA terms)? ;

naf_literals        :   naf_literal (COMMA naf_literals)? ;

naf_literal         :   NAF? classical_literal
                    |   builtin_atom ;

classical_literal   :   MINUS? ID (PAREN_OPEN terms? PAREN_CLOSE)? ;

builtin_atom        :   term relop term ;

relop               :   EQUAL
                    |   UNEQUAL
                    |   LESS
                    |   GREATER
                    |   LESS_OR_EQ
                    |   GREATER_OR_EQ
                    ;

terms               :   term (COMMA terms)? ;

term                :   ID
                    |   STRING
                    |   VARIABLE
                    |   ANONYMOUS_VARIABLE
                    |   PAREN_OPEN term PAREN_CLOSE
                    |   func_term
                    |   arith_term
                    ;

// functional terms
func_term           :   ID PAREN_OPEN terms? PAREN_CLOSE ;

// arithmetical terms (operator precedences built into the grammar)
arith_term          :   arith_sum ;

arith_sum           :   arith_prod
                    |   arith_sum PLUS arith_prod
                    |   arith_sum MINUS arith_prod
                    ;

arith_prod          :   arith_atom
                    |   arith_prod TIMES arith_atom
                    |   arith_prod DIV arith_atom 
                    ;

arith_atom          :  NUMBER
                    |  VARIABLE
                    |  MINUS arith_atom
                    |  PAREN_OPEN arith_sum PAREN_CLOSE
                    ;

/* lexer rules */

NAF                 :   'not' ; // define before ID to have precedence
ID                  :   [a-z][A-Za-z0-9_]* ;
VARIABLE            :   [A-Z][A-Za-z0-9_]* ;
STRING              :   '"' ( ~["] | ('\\"') )* '"' ;
NUMBER              :   '0' | [1-9][0-9]* ;
ANONYMOUS_VARIABLE  :   '_' ;
DOT                 :   '.' ;
COMMA               :   ',' ;
QUERY_MARK          :   '?' ;
COLON               :   ':' ;
SEMICOLON           :   ';' ;
OR                  :   '|' ;
CONS                :   ':-' ;
WCONS               :   ':~' ;
PLUS                :   '+' ;
MINUS               :   '-' ;
TIMES               :   '*' ;
DIV                 :   '/' ;
AT                  :   '@' ;
PAREN_OPEN          :   '(' ;
PAREN_CLOSE         :   ')' ;
SQUARE_OPEN         :   '[' ;
SQUARE_CLOSE        :   ']' ;
CURLY_OPEN          :   '{' ;
CURLY_CLOSE         :   '}' ;
EQUAL               :   '=' ;
UNEQUAL             :   '!=' ;
LESS                :   '<' ;
GREATER             :   '>' ;
LESS_OR_EQ          :   '<=' ;
GREATER_OR_EQ       :   '>=' ;
COUNT               :   '#count' ;
MAX                 :   '#max' ;
MIN                 :   '#min' ;
SUM                 :   '#sum' ;
COMMENT             :   '%' ~[\r\n]* -> skip ;
MULTI_LINE_COMMENT  :   '%*' .*? '*%' -> skip ;
BLANK               :   [ \t\n]+ -> skip ;