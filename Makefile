CC = gcc
CCFLAGS = -r -nostdlib -fno-builtin -fno-pie -fno-zero-initialized-in-bss -Wall -Werror-implicit-function-declaration -I $(SRC)
LDFLAGS =

SRC := .
OBJ := output

SOURCES := $(wildcard $(SRC)/*.c)
YRC1000OBJECTS := $(patsubst $(SRC)/%.c, $(OBJ)/YRC1000/%.o, $(SOURCES))
YRC1000OUTPUT = output/YRC1000/MotoRosYRC1_/MotoRosYRC1_191.out
YRC1000uOBJECTS := $(patsubst $(SRC)/%.c, $(OBJ)/YRC1000u/%.o, $(SOURCES))
YRC1000uOUTPUT = output/YRC1000u/MotoRosYRC1u_/MotoRosYRC1u_191.out

all: $(YRC1000OUTPUT) $(YRC1000uOUTPUT)

$(YRC1000OUTPUT): $(YRC1000OBJECTS)
	$(CC) $(CCFLAGS) $(LDFLAGS) -march=atom -m32 ParameterExtraction.yrcLib $^ -o $@

$(OBJ)/YRC1000/%.o: $(SRC)/%.c
	$(CC) $(CCFLAGS) -m32 -DYRC1000 -c $< -o $@

$(YRC1000uOUTPUT): $(YRC1000uOBJECTS)
	$(CC) $(CCFLAGS) $(LDFLAGS) -march=atom -m32 ParameterExtraction.yrcLib $^ -o $@

$(OBJ)/YRC1000u/%.o: $(SRC)/%.c
	$(CC) $(CCFLAGS) -m32 -DYRC1000u -c $< -o $@

.PHONY: clean
clean:
	rm -f $(YRC1000OBJECTS) $(YRC1000OUTPUT) $(YRC1000uOBJECTS) $(YRC1000uOUTPUT)
