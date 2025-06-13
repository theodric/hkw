/*
 * This program shows how to access the HKW PC - Funkuhr.
 * The receiver is also supported by xntpd.
 * (c) 1996 by St. Traby, GPL
 */

#include <stdio.h>
#include <termios.h>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>

void
sighandler (int sig)
{
	fprintf (stderr, "signal exit, signum=%d\n", sig);
	_exit (1);
}

static void
sleep_10ms (void)
{
	struct timeval tv;

	tv.tv_sec = 0;
	tv.tv_usec = 10000;
	select (0, NULL, NULL, NULL, &tv);
}

static int
writeclock (int fd, const char *msg)
{
	const char *x = msg;
	int err = 0;
	char y[22];

	errno = 0;
	while (!errno && *x) {
		if (write (fd, x, 1) != 1) {
			return x - msg;
		}
		read (fd, y, 1);
		sleep_10ms ();
		x++;
	}
	return x - msg - 1;
}

static int
readclock (int fd, char *buf)
{
	char *p = buf;

	errno = 0;
	do {
		read (fd, p, 1);
	} while (!errno && *p++ != '\r');
	return p - buf;
}

static int
openclock (const char *dev)
{
	int fd;
	struct termios t;

	fd = open (dev, O_RDWR);
	if (fd == -1) {
		fprintf (stderr, "open of \"%s\" failed, %m\n", dev);
		return fd;
	}
	t.c_iflag = IGNBRK | ISTRIP;
	t.c_oflag = 0;
	t.c_cflag = B300 | CS8 | CREAD | CLOCAL | CSTOPB;
	t.c_lflag = 0;
	t.c_cc[VMIN] = 1;
	t.c_cc[VTIME] = 0;

	if (tcsetattr (fd, TCSANOW, &t) == -1) {
		fprintf (stderr, "tcsetattr failed, %m\n", dev);
		close (fd);
		return -1;
	}

	return fd;
}

#define CHECK10(x) ((x) >= '0' && (x) <= '9')
#define CHECK5(x) ((x) >= '0' && (x) <= '5')
#define CHECK3(x) ((x) >= '0' && (x) <= '3')
#define CHECK2(x) ((x) >= '0' && (x) <= '2')
#define CHECK1(x) ((x) >= '0' && (x) <= '1')
#define CHECKW(x) ((x) >= '1' && (x) <= '7')
#define CHECK_UTC(x) 1
#define CHECK_STATUS(x) ((x) & 1)

static int
check_valid (const char *t)
{
	if (CHECK2 (t[0]) && CHECK10 (t[1]) && CHECK5 (t[2]) && CHECK10 (t[3])
	    && CHECK5 (t[4]) && CHECK10 (t[5]) && CHECKW (t[6])
	    && CHECK3 (t[7]) && CHECK10 (t[8]) && CHECK1 (t[9])
	    && CHECK10 (t[10]) && CHECK10 (t[11]) && CHECK10 (t[12])
	    && CHECK_UTC (t[13]) && CHECK_STATUS (t[14]) && t[15] == '\r')
		return 1;
	return 0;
}


static char *weekdays[] = { "Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Saturday",
	"Sunday"
};

static int
display_result (const char *t)
{
	int res;

	fprintf (stdout, "Time: %c%c:%c%c:%c%c\n", t[0], t[1], t[2], t[3],
		 t[4], t[5]);
	fprintf (stdout, "Date: %s 20%c%c-%c%c-%c%c\n",
		 (t[6] >= '1'
		  && t[6] < '8') ? weekdays[t[6] - '0' - 1] : "unknown",
		 t[11], t[12], t[9], t[10], t[7], t[8]);

	fprintf (stdout, "Time format: %s\n", (t[13] & 0x4) ? "UTC" : "MET");
	fprintf (stdout, "Low Battery: %s\n", (t[14] & 0x8) ? "yes" : "no");
	fprintf (stderr, "Valid-Bit  : information is %svalid\n",
		 (t[15] && 1) ? "" : "in");
	res = check_valid (t);
	fprintf (stderr, "Check-ok   : information looks %s\n",
		 (res) ? "ok" : "bad");
	return 1 - res;
}

int
main ()
{
	int fd, rc;
	char ret[255];

	signal (SIGALRM, sighandler);
	fd = openclock ("/dev/ttyUSB0");
	if (fd < 0)
		return 1;

	alarm (3);
	writeclock (fd, "o\r");
	rc = readclock (fd, ret);
	alarm (0);
	if (rc != 16) {
		fprintf (stderr, "expected 16 bytes, got %d\n", rc);
		return 1;
	}

	return display_result (ret);
}
