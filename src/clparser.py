from __future__ import annotations
from abc import abstractmethod
import re


class CmdIR:
    """
    Contains an intermediate representation of a command

    Args:
        cmd (str): the user entered command

    Attributes:
        name (str): the command name
        args (str): the command args splited by whitespace.
            `args` can contain command keys(-i, for example),
            because each command has own keys parser
        keys (dict[str, str]): the command keys

    """

    def __init__(self, cmd: str) -> None:
        self.name: str
        self.args: str
        self.keys: dict[str, str]

        self.name, self.args, self.keys = self.parseCmd(cmd)

    @abstractmethod
    def parseCmd(self, cmd: str) -> tuple[str, str, dict[str, str]]:
        """
        Split name, args and keys

        Args:
            cmd (str): the user entered command

        Returns:
            str: the command name
            str: the command args
            dict[str, str]: the command keys and its value

        Raises:
            SyntaxError

        """

        splitted = cmd.split()
        name = splitted[0]
        args = ' '.join(splitted[1:])

        return name, args, {}

    def __str__(self) -> str:
        def keysPrettyPrinter(keys: dict[str, str]) -> str:
            if not keys:
                return ''

            kpp = ''
            for k, v in keys.items():
                kv = f'{k} {v}'
                kv += ' ' if v else ''
                kpp += kv

            return kpp.rstrip()

        kpp: str = keysPrettyPrinter(self.keys)

        if kpp:
            return f'{self.name} {kpp} {self.args}'

        return f'{self.name} {self.args}'

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, CmdIR):
            return False

        return self.name == o.name \
            and self.args == o.args \
            and self.keys == self.keys


class GrepIR(CmdIR):
    """
    Intermediate representation for `grep` command.
    Grep can read from file and from result of
    previous command with pipe

    Supported keys for grep:
        -i -- match with case insensitive
        -w -- match the whole word
        -A n -- print n next lines after match

    """

    def __init__(self, cmd: str) -> None:
        self.name: str
        self.args: str
        self.keys: dict[str, str]

        self.name, self.args, self.keys = self.parseCmd(cmd)

    def parseCmd(self, cmd: str) -> tuple[str, str, dict[str, str]]:
        """
        Split name, args and keys

        Args:
            cmd (str): the user entered command

        Returns:
            str: the command name
            str: the command args
            dict[str, str]: the command keys and its value

        Raises:
            SyntaxError if there is unknown key
                or wrong syntax with `-A` key

        Supported keys for grep:
            -i -- match with case insensitive
            -w -- match the whole word
            -A n -- print n next lines after match

        """

        splitted = cmd.split()

        if len(splitted) < 2:
            raise SyntaxError(
                'grep: the command must be "grep [KEYS] pat [FILE]"')

        name = splitted[0]
        tokens = splitted[1:]

        args: str = ''
        keys: dict[str, str] = {}

        skipIteration = False
        errMsg = 'grep: after "-A" key a number must be, but found'

        for i in range(len(tokens)):
            if skipIteration:
                skipIteration = False
                continue

            tok: str = tokens[i]

            if tok == '-i' or tok == '-w':
                keys[tok] = ''
            elif tok == '-A':
                try:
                    val = tokens[i + 1]
                    if val.isnumeric():
                        keys['-A'] = val
                        skipIteration = True
                    else:
                        raise SyntaxError(f'{errMsg} {val}')
                except IndexError:
                    raise SyntaxError(f'{errMsg} nothing')
            # Unknown key
            elif tok[0] == '-':
                raise SyntaxError(f'grep: {tok}: Unknown key')
            else:
                args += (tok + ' ')

        return name, args.rstrip(), keys


class VarDecl:
    """
    Contains an intermediate representation
    of a variable declaration and methods
    for working with it

    Args:
        decl (str): the user entered decalration

    Attributes:
        var (str): the variable name
        value (str): the value of this variable

    """

    def __init__(self, decl: str) -> None:
        self.var: str
        self.value: str

        decl = decl.strip()
        splitPos = decl.find('=')
        self.var = decl[:splitPos]
        self.value = self.__parseQuotes(decl[splitPos + 1:])

    def __str__(self) -> str:
        return f'{self.var}={self.value}'

    @staticmethod
    def checkDecl(line: str) -> bool:
        """
        Check statement is variable decalartion

        Args:
            line (str): the user entered line

        Returns:
            bool: True if line is variable declaration, False otherwise

        """

        declRe = re.compile(r'[A-Za-z]\w*=([^|<>\'"]*|\'.*\'|\".*\")$')
        return bool(declRe.match(line))

    @staticmethod
    def parseDecl(line: str) -> VarDecl:
        """
        Wrapper for `VarDecl` constructor
        """
        return VarDecl(line)

    def __parseQuotes(self, value: str) -> str:
        if not value:
            return value

        if value[0] == '"' and value[-1] == '"':
            return value[1:-1]

        if value[0] == "'" and value[-1] == "'":
            return value[1:-1]

        return value


def getCmdParser(line: str) -> CmdIR:
    """
    Returns parser for current command

    """

    name: str = line.split()[0]

    if name == 'grep':
        return GrepIR(line)

    return CmdIR(line)


def createCmdIR(cmds: list[str]) -> list[CmdIR]:
    """
    Map suitable CmdIR to list[str]

    """

    return [getCmdParser(c) for c in cmds]


def parsePipes(line: str) -> list[str]:
    """
    Split the command with a pipe

    Args:
        line (str): the user entered line

    Returns:
        list[str]: the list of all commands between pipes

    """
    cmds = line.split('|')
    cmds = list(map(lambda c: c.rstrip(), cmds))
    cmds = list(map(lambda c: c.lstrip(), cmds))

    return cmds
