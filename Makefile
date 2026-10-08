CC      = gcc
CFLAGS  = -std=c17 -O2 -Wall -Wextra -pedantic
LDFLAGS =
TARGET  = prog
SRC     = main.c
OBJ     = $(SRC:.c=.o)

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(TARGET) $(OBJ)

.PHONY: all clean
