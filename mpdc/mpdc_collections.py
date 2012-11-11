# coding: utf-8
import sys
import shlex
import argparse

from mpdc.initialize import mpd, collectionsmanager, collections, colors
from mpdc.libs.utils import input_box, write_cache, esc_quotes, info, \
                            warning, colorize
from mpdc.libs.parser import parser


def display_songs(filenames, metadata=False, prefix=None):
    for song in filenames:
        if metadata:
            tags = ('artist', 'album', 'title')
            artist, album, title = mpd.get_tags(song, tags)
            print('%s - %s - %s' % (colorize(artist, colors[0]),
                                    colorize(album, colors[1]),
                                    colorize(title, colors[2])))
        elif prefix is not None:
            print(prefix + song)
        else:
            print(song)


def format_alias(alias):
    if 'mpd_playlist' in collections[alias]:
        return colorize('(playlist) ', colors[0]) + alias
    else:
        return alias


# --------------------------------
# Program functions
# --------------------------------

def ls(args):
    if args.collection is None:
        for alias in collections:
            print(format_alias(alias))
    else:
        display_songs(mpd.sort(parser.parse(args.collection)), args.m, args.p)


def show(args):
    if args.alias in collections:
        if 'mpd_playlist' in collections[args.alias]:
            info('This collection is stored as a MPD playlist\n')
        if 'expression' in collections[args.alias]:
            print(collections[args.alias]['expression'])
        if 'command' in collections[args.alias]:
            print('command: ' + collections[args.alias]['command'])
            print('--------\n')
        if 'songs' in collections[args.alias]:
            print('songs:')
            print('------')
            if 'mpd_playlist' not in collections[args.alias]:
                files = mpd.sort(collections[args.alias]['songs'])
            else:
                files = collections[args.alias]['songs']
            display_songs(files, args.m)
    else:
        warning('Stored collection [%s] doesn\'t exist' % args.alias)


def check(args):
    # will print a warning if there's a problem
    print('Checking "songs" sections...')
    collectionsmanager.feed(force=True)
    for alias in collections:
        if 'mpd_playlist' not in collections[alias]:
            print('Checking collection [%s]...' % alias)
            parser.parse('"' + esc_quotes(alias) + '"')


def find(args):
    # assuming it's a file
    if args.pattern in mpd.get_all_songs():
        print('File found in:')
        print('--------------')
        for alias in collections:
            songs_c = parser.parse('"' + esc_quotes(alias) + '"')
            if args.pattern in songs_c:
                print(format_alias(alias))

    # assuming it's a collection
    else:
        songs = parser.parse(args.pattern)
        print('Collection is a subset of:')
        print('--------------------------')
        if songs:
            for alias in collections:
                songs_c = parser.parse('"' + esc_quotes(alias) + '"')
                if args.pattern != alias and songs.issubset(songs_c):
                    print(format_alias(alias))


def add_songs(args):
    songs = parser.parse(args.collection)
    if songs:
        collectionsmanager.add_songs(args.alias, list(songs))


def remove_songs(args):
    songs = parser.parse(args.collection)
    if songs:
        collectionsmanager.remove_songs(args.alias, list(songs))


# --------------------------------
# Commands parser
# --------------------------------

def main():
    argparser = argparse.ArgumentParser(add_help=False)
    subparsers = argparser.add_subparsers()

    listsongs_parser = subparsers.add_parser('ls')
    listsongs_parser.add_argument('collection', nargs='?')
    listsongs_parser.add_argument('-m', action='store_true')
    listsongs_parser.add_argument('-p', action='store')
    listsongs_parser.set_defaults(func=ls)

    show_parser = subparsers.add_parser('show')
    show_parser.add_argument('alias')
    show_parser.add_argument('-m', action='store_true')
    show_parser.set_defaults(func=show)

    find_parser = subparsers.add_parser('find')
    find_parser.add_argument('pattern')
    find_parser.set_defaults(func=find)

    addsongs_parser = subparsers.add_parser('addsongs')
    addsongs_parser.add_argument('alias')
    addsongs_parser.add_argument('collection')
    addsongs_parser.set_defaults(func=add_songs)

    removesongs_parser = subparsers.add_parser('rmsongs')
    removesongs_parser.add_argument('alias')
    removesongs_parser.add_argument('collection')
    removesongs_parser.set_defaults(func=remove_songs)

    removesongs_parser = subparsers.add_parser('check')
    removesongs_parser.set_defaults(func=check)

    if len(sys.argv) == 1:
        cmd = input_box('mpdc-collections', 'Command for mpdc-collections:')
        if cmd is None or not cmd:
            sys.exit(0)
        if cmd.startswith('addsongs') or cmd.startswith('rmsongs'):
            lex = shlex.shlex(cmd, posix=True)
            lex.whitespace_split = True
            lex.commenters = ''
            cmd = [next(lex), next(lex), lex.instream.read()]
        else:
            cmd = cmd.split(' ', 1)
        args = argparser.parse_args(cmd)

    else:
        args = argparser.parse_args()

    args.func(args)

    if collectionsmanager.need_update:
        collectionsmanager.write_file()
        collectionsmanager.update_cache()
        write_cache('playlists', mpd.get_stored_playlists_info())

if __name__ == '__main__':
    main()