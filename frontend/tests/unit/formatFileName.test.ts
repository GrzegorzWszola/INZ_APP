import { describe, it, expect } from 'vitest';
import { formatFileName } from '../../src/components/file_upload';

describe('formatFileName', () => {
  it('returns empty string for empty input', () => {
    expect(formatFileName('')).toBe('');
  });

  it('formats simple hyphenated filename', () => {
    expect(formatFileName('my-book.epub')).toBe('My Book');
  });

  it('formats underscored filename', () => {
    expect(formatFileName('lord_of_the_rings.epub')).toBe('Lord Of The Rings');
  });

  it('handles filename with no extension', () => {
    expect(formatFileName('mybook')).toBe('Mybook');
  });

  it('formats filename with mixed separators', () => {
    expect(formatFileName('the-great_gatsby.epub')).toBe('The Great Gatsby');
  });

  it('lowercases everything after the first character (all-caps)', () => {
    expect(formatFileName('MY-BOOK.epub')).toBe('My Book');
  });

  it('strips from the LAST dot - intermediate dot treated as part of name', () => {
    // lastIndexOf('.') on "vol.1-book.epub" => strips ".epub"
    // remainder: "vol.1-book" => replace [-_] with space => "vol.1 book" => split on space
    // words: ["vol.1", "book"] => capitalize each => "Vol.1 Book"
    expect(formatFileName('vol.1-book.epub')).toBe('Vol.1 Book');
  });
});
