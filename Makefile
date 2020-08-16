CC = gcc
CCFLAGS = -r -nostdlib -fno-builtin -fno-zero-initialized-in-bss -Wall -Werror-implicit-function-declaration
LDFLAGS =

SRC := .
OBJ := output

SOURCES := $(wildcard $(SRC)/*.c)
YRC1000OBJECTS := $(patsubst $(SRC)/%.c, $(OBJ)/YRC1000/%.o, $(SOURCES))
YRC1000OUTPUT = output/YRC1000/MotoRosYRC1_/MotoRosYRC1_191.out

all: $(YRC1000OUTPUT)

$(YRC1000OUTPUT): $(YRC1000OBJECTS)
	$(CC) $(CCFLAGS) $(LDFLAGS) -m32 ParameterExtraction.yrcLib $^ -o $@

$(OBJ)/YRC1000/%.o: $(SRC)/%.c
	$(CC) $(CCFLAGS) -m32 -DYRC1000 -c $< -o $@

.PHONY: clean
clean:
	rm -f $(YRC1000OBJECTS) $(YRC1000OUTPUT)